CC=gcc
CFLAGS=-Wall -g

rvis: rvis.o 
	$(CC) $(CFLAGS) rvis.o -o rvis

clean:
	rm *.o rvis
