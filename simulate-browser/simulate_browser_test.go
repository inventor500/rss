package simulate_browser_test

import (
	"compress/gzip"
	"fmt"
	"io"
	"net/http"
	"net/http/httptest"
	"testing"

	sim "github.com/inventor500/rss/simulate-browser"
)

func TestDownloadFile(t *testing.T) {
	const response = "<html><body>Hello world!</body></html>"
	const userAgent = "Test User Agent"
	t.Run("Headers", func(t *testing.T) {
		const path = "/test-path"
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Not much point in testing everything, since these might be changed
			if r.URL.Path != path {
				t.Errorf("Expected path %s, received %s", path, r.URL.Path)
			}
			if r.Header.Get("Accept-Encoding") != "gzip" {
				t.Errorf("Expected Accept-Encoding 'gzip', received %s", r.Header.Get("Accept-Encoding"))
			}
			if r.Header.Get("User-Agent") != userAgent {
				t.Errorf("Expected user-agent %s, received %s", userAgent, r.Header.Get("User-Agent"))
			}
			if r.Header.Get("DNT") != "1" {
				t.Errorf("Expected DNT value 1, received %s", r.Header.Get("DNT"))
			}
			if r.Header.Get("Sec-GPC") != "1" {
				t.Errorf("Expected Sec-GPC value 1, recieved %s", r.Header.Get("Sec-GPC"))
			}
			io.WriteString(w, response)
		}))
		defer server.Close()
		_, err := sim.DownloadFile(server.URL+path, 0, userAgent, false)
		if err != nil {
			t.Errorf("Received error %s", err)
		}
	})

	t.Run("Response - No compression", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			io.WriteString(w, response)
		}))
		defer server.Close()
		res, err := sim.DownloadFile(server.URL, 0, userAgent, false)
		if err != nil {
			t.Errorf("Received error %s", err)
		}
		if res != response {
			t.Errorf("Expected response %s, received %s", response, res)
		}
	})

	t.Run("Response - Gzip", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Gzip the response
			w.Header().Set("Content-Encoding", "gzip")
			writer := gzip.NewWriter(w)
			writer.Write([]byte(response))
			writer.Close()
		}))
		defer server.Close()
		res, err := sim.DownloadFile(server.URL, 0, userAgent, false)
		if err != nil {
			t.Errorf("Received an error: %s", err)
		}
		if res != response {
			t.Errorf("Expected response %s, received %s", response, res)
		}
	})
	t.Run("Invalid Error Code", func(t *testing.T) {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			http.NotFound(w, r)
		}))
		defer server.Close()
		_, err := sim.DownloadFile(server.URL, 0, userAgent, false)
		expected := "received status code 404"
		if err == nil || fmt.Sprintf("%s", err) != expected {
			t.Errorf("Expected error to be %s, got %s", expected, err)
		}
	})
}
