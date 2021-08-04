CC=gcc
CFLAGS=-Wall -g

rvis: rvis.o #elfreader.o
	$(CC) $(CFLAGS) rvis.o -o rvis

# elfreader.o -o rvis

#rvis.o: rvis.c rv32.h bitmanip.h elfreader.h
#	$(CC) $(CFLAGS) -c rvis.c

#elfreader.o: elfreader.c elfreader.h
#	$(CC) $(CFLAGS) -c  elfreader.c

clean:
	rm *.o rvis
