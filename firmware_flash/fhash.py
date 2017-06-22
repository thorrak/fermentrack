import hashlib


def hash_bytestr_iter(bytesiter, hasher, ashexstr=False):
    for block in bytesiter:
        hasher.update(block)
    return (hasher.hexdigest() if ashexstr else hasher.digest())


def file_as_blockiter(afile, blocksize=65536):
    with afile:
        block = afile.read(blocksize)
        while len(block) > 0:
            yield block
            block = afile.read(blocksize)


# hash_of_file takes a file name, and returns the text sha256 hash of the file (for confirming file validity)
def hash_of_file(fname):
    return hash_bytestr_iter(file_as_blockiter(open(fname, 'rb')), hashlib.sha256(), True)
