package article_getter

/*
#cgo pkg-config: tidy
#include "tidy.h"
#include <stdlib.h>
*/
import "C"
import (
	"errors"
	"unsafe"
)

func convertToXML(html string) (string, error) {
	cstr := C.CString(html)
	defer C.free(unsafe.Pointer(cstr))
	result := C.convertToXML(cstr)
	if result != nil {
		return C.GoString(result), nil
	}
	return "", errors.New("unable to convert document")
}
