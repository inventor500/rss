package main

import (
	"log"
	"log/syslog"
)

func initLog() error {
	sysl, err := syslog.New(syslog.LOG_INFO, "FetchArticleContents")
	if err != nil {
		return err
	}
	log.SetOutput(sysl)
	log.SetFlags(0)
	return nil
}
