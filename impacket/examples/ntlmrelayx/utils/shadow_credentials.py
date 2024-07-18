from struct import pack
from Cryptodome.Util.number import long_to_bytes
from OpenSSL.crypto import PKey, X509
import base64
import uuid
import datetime
import time

def getTicksNow():
    diff_seconds = int( (datetime.datetime(1970,1,1) - datetime.datetime(1601,1,1)).total_seconds() )
    return ( time.time_ns() + (diff_seconds * 1e9) ) // 100

def getDeviceId():
    return uuid.uuid4().bytes

def createSelfSignedX509Certificate(subject,kSize=2048,nBefore,nAfter):
    key = PKey()
    key.generate_key(pkey_type=PKey.TYPE_RSA, size=kSize)

    cert = X509()

    cert.get_subject().CN = subject
    cert.set_issuer(cert.get_subject())
    cert.gmtime_adj_notBefore(nBefore)
    cert.gmtime_adj_notAfter(nAfter)
    cert.set_pubkey(key)

    cert.sign(key, hash_algo="sha256")
    return key,certificate

class KeyCredential():
    @staticmethod
    def raw_public_key(certificate,key):
        pem_public_key = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        public_key = RSA.importKey(pem_public_key)

        kSize = pack("<I",public_key.size_in_bits())
        exponent = long_to_bytes(public_key.e)
        exponentSize += pack("<I",len(exponent))
        modulus = long_to_bytes(public_key.m)
        modulusSize += pack("<I",len(modulus))

        padding = pack("<I",0)*2

        return b'RSA1' + kSize + exponentSize + modulusSize + padding + exponent + modulus

    def __init__(self,certificate,key,deviceId,currentTime):
        self.__publicKey = self.raw_public_key(certificate,key)
        self.__rawKeyMaterial = (0x3,self.__publicKey)
        self.__usage = (0x4,pack("<B",0x01))
        self.__source = (0x5,pack("<B",0x0))
        self.__deviceId = (0x6,deviceId)
        self.__customKeyInfo = (0x7,pack("<BB",0x1,0x0))
        currentTime = pack("<Q",currentTime)
        self.__lastLogonTime = (0x8,pack("<Q",currentTime))
        self.__creationTime = (0x9,pack("<Q",currentTime))

        self.__version = 0x200

        self.__sha256 = base64.b64encode( hashlib.sha256(self.__publickey).digest() ).decode("utf-8")

    def __packData(self,fields):
        return b''.join( pack("<HB",len(field[1]),field[0]) + field[1] for field in fields] )
    def __getKeyIndetifier(self):
        self.__identifier = base64.b64decode( self.__sha256+"===" )
        return (0x1,self.__identifier)

    def __getKeyHash(self):
        computed_hash = hashlib.sha256(self.__identifier).digest()
        return (0x2,computed_hash)

    def dumpBinary(self):
        version = pack("<L",self.__version)

        binaryData = self.__packData( [self.__getKeyIdentifier(),
                                        self.__getKeyHash(),
                                      ])

        binaryProperties = self.__packData( [self.__rawKeyMaterial,
                            self.__usage,
                            self.__source,
                            self.__deviceId,
                            self.__customKeyInfo,
                            self.__lastLogonTime,
                            self.__creationTime,
                         ])

        return version + binaryData + binaryProperties


def toDNWithBinary2String( binaryData, owner ):
    hexdata = binascii.hexlify(binaryData).decode("UTF-8")
    return "B:%d:%s:%s" % (len(binaryData)*2,hexdata,owner)


def exportPFX(certificate,key,path_to_file,password):
    if len(os.path.dirname(path_to_file)) != 0:
        if not os.path.exists(os.path.dirname(path_to_file)):
            os.makedirs(os.path.dirname(path_to_file), exist_ok=True)

    pk = OpenSSL.crypto.PKCS12()
    pk.set_privatekey(key)
    pk.set_certificate(certificate)
    with open(path_to_file+".pfx","wb") as f:
        f.write(pk.export(passphrase=password))


def exportPEM(certificate,key, path_to_files):
    if len(os.path.dirname(path_to_files)) != 0:
        if not os.path.exists(os.path.dirname(path_to_files)):
            os.makedirs(os.path.dirname(path_to_files), exist_ok=True)

        cert = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, certificate)
        with open(path_to_files + "_cert.pem", "wb") as f:
            f.write(cert)
        privpem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, key)
        with open(path_to_files + "_priv.pem", "wb") as f:
            f.write(privpem)

