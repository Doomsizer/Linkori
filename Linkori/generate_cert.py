from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import os
import ipaddress

# Создаем директорию для сертификатов, если она не существует
os.makedirs('certs', exist_ok=True)

# Генерация приватного ключа
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# Сохраняем приватный ключ в файл
with open('certs/private.key', 'wb') as f:
    f.write(private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ))

# Создание информации о владельце и издателе сертификата
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"RU"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"Moscow"),
    x509.NameAttribute(NameOID.LOCALITY_NAME, u"Moscow"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Linkori"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
])

# Создание сертификата
cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    private_key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    # Сертификат действителен 365 дней
    datetime.datetime.utcnow() + datetime.timedelta(days=365)
).add_extension(
    x509.SubjectAlternativeName([
        x509.DNSName(u"localhost"),
        x509.IPAddress(ipaddress.IPv4Address(u"127.0.0.1")),
    ]),
    critical=False,
).sign(private_key, hashes.SHA256())

# Сохраняем сертификат в файл
with open('certs/certificate.pem', 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

# Создадим также копию для cert.pem, который также используется в проекте
with open('certs/cert.pem', 'wb') as f:
    f.write(cert.public_bytes(serialization.Encoding.PEM))

print("Сертификаты успешно созданы:")
print("1. certs/private.key - приватный ключ")
print("2. certs/certificate.pem - сертификат")
print("3. certs/cert.pem - копия сертификата")