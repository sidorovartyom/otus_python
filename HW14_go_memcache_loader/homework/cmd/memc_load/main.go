package main

import (
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/otus/memc_load/internal/loader"
)

type Config struct {
	Pattern  string
	IdfaAddr string
	GaidAddr string
	AdidAddr string
	DvidAddr string
	Workers  int
	DryRun   bool
	LogFile  string
}

func parseFlags() *Config {
	cfg := &Config{}

	flag.StringVar(&cfg.Pattern, "pattern", "./data/*.tsv.gz", "pattern for log files")
	flag.StringVar(&cfg.IdfaAddr, "idfa", "127.0.0.1:33013", "memcache address for idfa")
	flag.StringVar(&cfg.GaidAddr, "gaid", "127.0.0.1:33014", "memcache address for gaid")
	flag.StringVar(&cfg.AdidAddr, "adid", "127.0.0.1:33015", "memcache address for adid")
	flag.StringVar(&cfg.DvidAddr, "dvid", "127.0.0.1:33016", "memcache address for dvid")
	flag.IntVar(&cfg.Workers, "workers", 4, "number of worker goroutines")
	flag.BoolVar(&cfg.DryRun, "dry", false, "dry run mode (don't write to memcache)")
	flag.StringVar(&cfg.LogFile, "log", "", "log file path (default: stdout)")

	flag.Parse()
	return cfg
}

// dotRename renames file by prefixing with dot (marks as processed)
func dotRename(path string) error {
	dir := filepath.Dir(path)
	filename := filepath.Base(path)

	// Don't rename if already starts with dot
	if strings.HasPrefix(filename, ".") {
		return nil
	}

	newPath := filepath.Join(dir, "."+filename)
	return os.Rename(path, newPath)
}

// getFilesInOrder returns files matching pattern sorted by name (chronological order)
func getFilesInOrder(pattern string) ([]string, error) {
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return nil, fmt.Errorf("failed to glob pattern: %w", err)
	}

	// Filter out files that already start with dot (already processed)
	var files []string
	for _, match := range matches {
		filename := filepath.Base(match)
		if !strings.HasPrefix(filename, ".") {
			files = append(files, match)
		}
	}

	// Sort files by name to ensure chronological processing
	sort.Strings(files)

	return files, nil
}

func main() {
	cfg := parseFlags()

	// Setup logging
	if cfg.LogFile != "" {
		file, err := os.OpenFile(cfg.LogFile, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0666)
		if err != nil {
			log.Fatalf("Failed to open log file: %v", err)
		}
		defer file.Close()
		log.SetOutput(file)
	}

	log.Printf("Memc loader started with pattern: %s, workers: %d, dry-run: %v",
		cfg.Pattern, cfg.Workers, cfg.DryRun)

	// Get files in chronological order
	files, err := getFilesInOrder(cfg.Pattern)
	if err != nil {
		log.Fatalf("Failed to get files: %v", err)
	}

	if len(files) == 0 {
		log.Printf("No files matching pattern: %s", cfg.Pattern)
		return
	}

	log.Printf("Found %d files to process", len(files))

	// Device memcache mapping
	deviceMemc := map[string]string{
		"idfa": cfg.IdfaAddr,
		"gaid": cfg.GaidAddr,
		"adid": cfg.AdidAddr,
		"dvid": cfg.DvidAddr,
	}

	// Create loader
	ml := loader.NewMemcLoader(deviceMemc, cfg.Workers, cfg.DryRun)
	defer ml.Close()

	// Process files sequentially (to maintain chronological order)
	var totalProcessed, totalErrors uint64

	for _, file := range files {
		stats, err := ml.ProcessFile(file)
		if err != nil {
			log.Printf("ERROR: Failed to process file %s: %v", file, err)
			continue
		}

		totalProcessed += stats.Processed
		totalErrors += stats.Errors

		// Rename file after successful processing
		if err := dotRename(file); err != nil {
			log.Printf("WARNING: Failed to rename file %s: %v", file, err)
		} else {
			log.Printf("File renamed: %s", file)
		}
	}

	log.Printf("All files processed. Total: %d records, %d errors", totalProcessed, totalErrors)
}
