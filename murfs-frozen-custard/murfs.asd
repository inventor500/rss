(asdf:defsystem "murfs"
  :depends-on ("plump" "dexador" "local-time")
  :components ((:file "main"))
  :build-pathname "murfs"
  :entry-point "murfs:main")

