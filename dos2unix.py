
def dos2unix(in_file, out_file):
  outsize = 0
  with open(in_file, 'rb') as infile:
    content = infile.read()
    print(content)
  with open(out_file, 'wb') as output:
    for line in content.splitlines():
      outsize += len(line) + 1
      output.write(line + '\n'.encode())

  print("Done. Saved %s bytes." % (len(content)-outsize))
