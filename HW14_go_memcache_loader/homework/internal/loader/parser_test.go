package loader

import (
	"testing"
)

func TestParseLine(t *testing.T) {
	tests := []struct {
		name    string
		line    string
		wantErr bool
	}{
		{
			name:    "valid line",
			line:    "idfa\te7e1a50c0ec2747ca56cd9e1558c0d7c\t67.7835424444\t-22.8044005471\t1,2,3,4,5",
			wantErr: false,
		},
		{
			name:    "empty dev_type",
			line:    "\te7e1a50c0ec2747ca56cd9e1558c0d7c\t67.7835424444\t-22.8044005471\t1,2,3",
			wantErr: true,
		},
		{
			name:    "invalid latitude",
			line:    "idfa\te7e1a50c0ec2747ca56cd9e1558c0d7c\tinvalid\t-22.8044005471\t1,2,3",
			wantErr: true,
		},
		{
			name:    "too few fields",
			line:    "idfa\te7e1a50c0ec2747ca56cd9e1558c0d7c\t67.7835424444",
			wantErr: true,
		},
	}

	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			ai, err := ParseLine(tt.line)
			if (err != nil) != tt.wantErr {
				t.Errorf("ParseLine() error = %v, wantErr %v", err, tt.wantErr)
				return
			}
			if !tt.wantErr && ai == nil {
				t.Errorf("ParseLine() returned nil for valid line")
			}
		})
	}
}

func TestAppsInstalled_Key(t *testing.T) {
	ai := &AppsInstalled{
		DevType: "idfa",
		DevID:   "test123",
		Lat:     10.5,
		Lon:     20.3,
		Apps:    []uint32{1, 2, 3},
	}

	expected := "idfa:test123"
	if got := ai.Key(); got != expected {
		t.Errorf("Key() = %v, want %v", got, expected)
	}
}

func TestAppsInstalled_ToProtobuf(t *testing.T) {
	ai := &AppsInstalled{
		DevType: "idfa",
		DevID:   "test123",
		Lat:     10.5,
		Lon:     20.3,
		Apps:    []uint32{1, 2, 3},
	}

	userApps := ai.ToProtobuf()
	if userApps == nil {
		t.Error("ToProtobuf() returned nil")
		return
	}

	if len(userApps.Apps) != 3 {
		t.Errorf("ToProtobuf() apps length = %v, want 3", len(userApps.Apps))
	}

	if userApps.GetLat() != 10.5 {
		t.Errorf("ToProtobuf() lat = %v, want 10.5", userApps.GetLat())
	}

	if userApps.GetLon() != 20.3 {
		t.Errorf("ToProtobuf() lon = %v, want 20.3", userApps.GetLon())
	}
}

func TestParseLineWithInvalidApps(t *testing.T) {
	// Line with some invalid app IDs
	line := "gaid\t3261cf44cbe6a00839c574336fdf49f6\t137.790839567\t56.8403675248\t123,abc,456,xyz,789"

	ai, err := ParseLine(line)
	if err != nil {
		t.Errorf("ParseLine() should not error on invalid apps: %v", err)
		return
	}

	// Should have parsed only valid app IDs: 123, 456, 789
	if len(ai.Apps) != 3 {
		t.Errorf("ParseLine() parsed %d apps, want 3", len(ai.Apps))
	}

	expected := []uint32{123, 456, 789}
	for i, app := range ai.Apps {
		if app != expected[i] {
			t.Errorf("ParseLine() app[%d] = %d, want %d", i, app, expected[i])
		}
	}
}
