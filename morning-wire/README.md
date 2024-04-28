# Morning Wire

The Morning Wire podcast feed has multiple redirects before it reaches the real URL. Because some of the future URLs are included in the redirects, this uses a regex find-and-replace to reduce the number of redirects to one.

This script invokes the `simulate-browser` executable from the same repository, and assumes that executable is in `$PATH`.

## Usage

This can be executed using Newsboat's `exec` in the URLs file:

```
exec:~/path/to/script "~Morning Wire"
```

## Limitations

* This will not follow Newsboat's proxy settings.
