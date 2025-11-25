package loader

import (
	"fmt"
	"log"
	"sync"
	"sync/atomic"
	"time"

	"github.com/bradfitz/gomemcache/memcache"
)

const (
	NormalErrRate = 0.01
)

// MemcLoader handles loading data to memcache
type MemcLoader struct {
	DeviceMemc map[string]string // device type -> memcache address
	Workers    int
	DryRun     bool
	clients    map[string]*memcache.Client
	clientsMux sync.RWMutex
}

// Statistics holds processing statistics
type Statistics struct {
	Processed uint64
	Errors    uint64
}

// NewMemcLoader creates a new loader instance
func NewMemcLoader(deviceMemc map[string]string, workers int, dryRun bool) *MemcLoader {
	return &MemcLoader{
		DeviceMemc: deviceMemc,
		Workers:    workers,
		DryRun:     dryRun,
		clients:    make(map[string]*memcache.Client),
	}
}

// getClient returns memcache client for device type (thread-safe, with caching)
func (ml *MemcLoader) getClient(devType string) (*memcache.Client, error) {
	ml.clientsMux.RLock()
	client, exists := ml.clients[devType]
	ml.clientsMux.RUnlock()

	if exists {
		return client, nil
	}

	// Create new client
	ml.clientsMux.Lock()
	defer ml.clientsMux.Unlock()

	// Double-check after acquiring write lock
	if client, exists := ml.clients[devType]; exists {
		return client, nil
	}

	addr, ok := ml.DeviceMemc[devType]
	if !ok {
		return nil, fmt.Errorf("unknown device type: %s", devType)
	}

	client = memcache.New(addr)
	client.Timeout = 3 * time.Second
	ml.clients[devType] = client

	return client, nil
}

// insertAppsInstalled inserts single record to memcache
func (ml *MemcLoader) insertAppsInstalled(ai *AppsInstalled) error {
	if ml.DryRun {
		log.Printf("[DRY RUN] %s -> apps: %v, lat: %.2f, lon: %.2f", ai.Key(), ai.Apps, ai.Lat, ai.Lon)
		return nil
	}

	client, err := ml.getClient(ai.DevType)
	if err != nil {
		return err
	}

	userApps := ai.ToProtobuf()
	packed, err := userApps.Serialize()
	if err != nil {
		return fmt.Errorf("failed to serialize protobuf: %w", err)
	}

	item := &memcache.Item{
		Key:   ai.Key(),
		Value: packed,
	}

	if err := client.Set(item); err != nil {
		return fmt.Errorf("failed to set memcache: %w", err)
	}

	return nil
}

// worker processes lines from channel
func (ml *MemcLoader) worker(id int, lines <-chan string, stats *Statistics, wg *sync.WaitGroup) {
	defer wg.Done()

	for line := range lines {
		ai, err := ParseLine(line)
		if err != nil {
			atomic.AddUint64(&stats.Errors, 1)
			continue
		}

		if err := ml.insertAppsInstalled(ai); err != nil {
			atomic.AddUint64(&stats.Errors, 1)
			log.Printf("Worker %d: failed to insert %s: %v", id, ai.Key(), err)
		} else {
			atomic.AddUint64(&stats.Processed, 1)
		}
	}
}

// ProcessFile processes a single gzip file
func (ml *MemcLoader) ProcessFile(filename string) (*Statistics, error) {
	log.Printf("Processing file: %s", filename)

	stats := &Statistics{}
	lines, errors := ReadGzipFile(filename)

	// Start workers
	var wg sync.WaitGroup
	for i := 0; i < ml.Workers; i++ {
		wg.Add(1)
		go ml.worker(i, lines, stats, &wg)
	}

	// Wait for workers to finish
	wg.Wait()

	// Check for file reading errors
	select {
	case err := <-errors:
		if err != nil {
			return stats, err
		}
	default:
	}

	// Calculate error rate
	processed := atomic.LoadUint64(&stats.Processed)
	errorCount := atomic.LoadUint64(&stats.Errors)

	if processed > 0 {
		errRate := float64(errorCount) / float64(processed)
		if errRate < NormalErrRate {
			log.Printf("Acceptable error rate (%.4f). Successful load", errRate)
		} else {
			log.Printf("High error rate (%.4f > %.4f). Failed load", errRate, NormalErrRate)
		}
	}

	log.Printf("File processed: %d records, %d errors", processed, errorCount)

	return stats, nil
}

// Close closes all memcache connections
func (ml *MemcLoader) Close() {
	ml.clientsMux.Lock()
	defer ml.clientsMux.Unlock()

	for _, client := range ml.clients {
		// gomemcache doesn't have explicit Close method
		// connections will be closed when client is garbage collected
		_ = client
	}
	ml.clients = make(map[string]*memcache.Client)
}
