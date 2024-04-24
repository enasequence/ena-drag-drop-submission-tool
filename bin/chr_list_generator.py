import fnmatch
import os
import gzip
import codecs

class Chr_list_generator:

    def __init__(self, output):
        self.output = output

    def chromosome_list(self):
        for file in os.listdir(self.output):
            if fnmatch.fnmatch(file, '*.fasta.gz*'):
                with gzip.open(f'{self.output}/{file}', 'r') as f:
                    first_line = codecs.decode(f.readline()).strip('>').strip('\n')
                    print(first_line)
                with gzip.open(f'{self.output}/{file.strip("*.fasta.gz*")}_chromosomelist.txt.gz', 'wb') as f:
                    string = f'{first_line.strip()}\t{int(1)}\tMonopartite'
                    f.write(codecs.encode(string))


