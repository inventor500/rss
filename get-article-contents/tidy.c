#include "tidy.h"
#include <tidy.h>
#include <tidybuffio.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>

char* convertToXML(const char* html) {
  TidyBuffer out = {0};
  TidyBuffer err = {0};
  int rc = -1;
  Bool ok;
  TidyDoc tdoc = tidyCreate();
  ok = tidyOptSetBool(tdoc, TidyXhtmlOut, yes)       // Use XML
    && tidyOptSetBool(tdoc, TidyXmlDecl, yes)        // Turn on the XML declaration
    && tidyOptSetBool(tdoc, TidyNumEntities, yes)    // Prevent parsing errors from Go
    && tidyOptSetBool(tdoc, TidyBodyOnly, yes)       // Only export the elements this was given
    && tidyOptSetBool(tdoc, TidyHideComments, yes);  // Remove comments
  if (ok) rc = tidySetErrorBuffer(tdoc, &err);
  if (rc >= 0) {
    rc = tidyParseString(tdoc, html);
  }
  if (rc >= 0) {
    rc = tidyCleanAndRepair(tdoc);
  }
  if (rc >= 0) {
    tidyRunDiagnostics(tdoc);
  }
  if (rc > 1) {
    rc = (tidyOptSetBool(tdoc, TidyForceOutput, yes) ? rc : -1);
  }
  if (rc >= 0) {
    rc = tidySaveBuffer(tdoc, &out);
  }
  char* output = NULL;
  if (rc >= 0) {
    // +1 is really necessary here
    output = malloc(out.size * sizeof(char) + 1);
    if (!output) {
      tidyBufFree(&out);
      tidyBufFree(&err);
      tidyRelease(tdoc);
      return NULL;
    }
    strcpy(output, out.bp);
  }
  tidyBufFree(&out);
  tidyBufFree(&err);
  tidyRelease(tdoc);
  return output;
}
