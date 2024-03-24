murfs: main.lisp murfs.asd
	sbcl --load murfs.asd\
	     --eval '(ql:quickload :murfs)'\
	     --eval "(sb-ext:save-lisp-and-die #p\"murfs\" :toplevel #'murfs:main :executable t :compression 22)"
