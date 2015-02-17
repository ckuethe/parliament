#!/bin/sh

# http://graphviz.org/doc/info/shapes.html#polygon
# http://graphviz.org/doc/info/attrs.html#d:shape

( \
	echo "graph {" ; \
	echo 'graph [size="18,10" fontsize=7 splines=polyline ]' ; \
	echo 'edge [penwidth=0.25]' ; \
	echo 'node [shape=point size=2]' ; \
	cat network.txt | sort -u ; \
	echo "}"; \
) | time dot -x -Kneato -Tsvg -onetwork.svg

convert -density 150 -size 1280x800 network.svg network.png
