#!/bin/bash

if [ $# -eq 0 ]
then
	python3 ./game.py
elif [ $1 = "-t" ]
then
	if [ $2 = "-n" ]
	then
		for (( count=0; count< $3; count++ ))
			do
			python3 ./game.py -t -p={"$count"} &
		done
	else
		python3 ./game.py -t
	fi
fi
