package loader

import (
	"bufio"
	"compress/gzip"
	"fmt"
	"os"
	"strconv"
	"strings"

	"github.com/otus/memc_load/internal/appsinstalled"
)

// AppsInstalled represents parsed line from TSV file
type AppsInstalled struct {
	DevType string
	DevID   string
	Lat     float64
	Lon     float64
	Apps    []uint32
}

// ParseLine parses a single TSV line
// Format: dev_type\tdev_id\tlat\tlon\tapp1,app2,app3...
func ParseLine(line string) (*AppsInstalled, error) {
	parts := strings.Split(strings.TrimSpace(line), "\t")
	if len(parts) < 5 {
		return nil, fmt.Errorf("invalid line format: expected 5 fields, got %d", len(parts))
	}

	devType := parts[0]
	devID := parts[1]

	if devType == "" || devID == "" {
		return nil, fmt.Errorf("empty dev_type or dev_id")
	}

	lat, err := strconv.ParseFloat(parts[2], 64)
	if err != nil {
		return nil, fmt.Errorf("invalid latitude: %w", err)
	}

	lon, err := strconv.ParseFloat(parts[3], 64)
	if err != nil {
		return nil, fmt.Errorf("invalid longitude: %w", err)
	}

	// Parse apps list
	rawApps := strings.Split(parts[4], ",")
	apps := make([]uint32, 0, len(rawApps))

	for _, appStr := range rawApps {
		appStr = strings.TrimSpace(appStr)
		if appStr == "" {
			continue
		}

		app, err := strconv.ParseUint(appStr, 10, 32)
		if err != nil {
			// Skip invalid apps but continue processing
			continue
		}
		apps = append(apps, uint32(app))
	}

	return &AppsInstalled{
		DevType: devType,
		DevID:   devID,
		Lat:     lat,
		Lon:     lon,
		Apps:    apps,
	}, nil
}

// ToProtobuf converts AppsInstalled to protobuf UserApps
func (ai *AppsInstalled) ToProtobuf() *appsinstalled.UserApps {
	return appsinstalled.NewUserApps(ai.Apps, ai.Lat, ai.Lon)
}

// Key returns the memcache key (dev_type:dev_id)
func (ai *AppsInstalled) Key() string {
	return fmt.Sprintf("%s:%s", ai.DevType, ai.DevID)
}

// ReadGzipFile reads and returns lines from a gzip file
func ReadGzipFile(filename string) (chan string, chan error) {
	lines := make(chan string, 1000)
	errors := make(chan error, 1)

	go func() {
		defer close(lines)
		defer close(errors)

		file, err := os.Open(filename)
		if err != nil {
			errors <- fmt.Errorf("failed to open file: %w", err)
			return
		}
		defer file.Close()

		gzReader, err := gzip.NewReader(file)
		if err != nil {
			errors <- fmt.Errorf("failed to create gzip reader: %w", err)
			return
		}
		defer gzReader.Close()

		scanner := bufio.NewScanner(gzReader)
		// Set buffer size to handle long lines
		buf := make([]byte, 0, 64*1024)
		scanner.Buffer(buf, 1024*1024)

		for scanner.Scan() {
			line := scanner.Text()
			if line != "" {
				lines <- line
			}
		}

		if err := scanner.Err(); err != nil {
			errors <- fmt.Errorf("scanner error: %w", err)
		}
	}()

	return lines, errors
}
