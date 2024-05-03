package main_test

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"testing"
)

// Name of the executable to build
var name = "simulate-browser"

func TestMain(m *testing.M) {
	if runtime.GOOS == "windows" {
		name += ".exe"
	}
	fmt.Fprintln(os.Stderr, "Building executable...")
	build := exec.Command("go", "build", "-o", name)
	if err := build.Run(); err != nil {
		fmt.Fprintf(os.Stderr, "Failed to build executable: %s", err)
		os.Exit(1)
	}
	fmt.Println("Running tests...")

	result := m.Run()

	fmt.Fprintln(os.Stderr, "Cleaning up...")
	os.Remove(name)

	os.Exit(result)
}

func TestExecutable(t *testing.T) {
	dir, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(dir, name) // Path of the executable
	t.Run("Test Basic Usage", func(t *testing.T) {
		const response = "<html><body>Hello world!</body></html>"
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			_, err := w.Write([]byte(response))
			if err != nil {
				t.Fatalf("Failed to send response: %s", err)
			}
		}))
		defer server.Close()
		output, err := exec.Command(path, server.URL).Output()
		if err != nil {
			t.Errorf("%s", err)
		}
		if string(output) != response+"\n" {
			t.Errorf("Expected '%s', received '%s'", response, output)
		}
	})
}
