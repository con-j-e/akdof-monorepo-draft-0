↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

# About
Resources for SSL verification on the State of Alaska network.

# Contents
### `root/`
Contains the Zscaler root certificate.

### `chain/`
Contains certificate chains that can be used for SSL verification with specific HTTPS endpoints.
All certificate chains use the naming convention `{host}:{port}_chain.pem`.

# Creating Custom Certificate Chains for use on the SOA Network
Self-signed certificate errors can occur when SSL is used to verify connections made over HTTPS between the SOA network and an external endpoint.
Tools / libraries used to make connections may offer the ability to specify a custom certification file to verify the connection.
Using `openssl s_client` to retrieve broken certificate chains and adding the Zscaler root certificate to the bottom of the chain is an effective way to create custom certificate chains that work for SSL verification.

## Getting OpenSSL for Windows
FireDaemon provides [binary distributions of OpenSSL for Microsoft Windows](https://kb.firedaemon.com/support/solutions/articles/4000121705#Windows-Installer) that can be installed as an executable (.exe). This is the easiest way to get up and running with OpenSSL.

## Using OpenSSL CLI to Retrieve a Broken Certificate Chain
The `s_client` command is documented [here](https://docs.openssl.org/1.0.2/man1/s_client/#description).

***Examples***

`openssl s_client -connect=github.com:443 -showcerts`

`openssl s_client -connect=services.sentinel-hub.com:443 -showcerts`

`openssl s_client -connect=maps.matsugov.us:443 -showcerts`

`openssl s_client -connect anaconda.org:443 -showcerts`

`openssl s_client -connect pypi.org:443 -showcerts`

## Getting the Zscaler Root Certificate
Download "Windows Zscaler Root CA Certificate" from [SOA OIT](https://oit-int.alaska.gov/security/zscaler).

## Creating a Custom .pem File
1. Open a blank file in your editor of choice. After completing steps 2 - 5, the file should be saved with a `.pem` file extension.
2. Copy the output of a `openssl s_client -connect={host}:{port} -showcerts` command and paste it into the file.
3. Delete content below the final -----END CERTIFICATE----- line.
4. Copy content from the Zscaler root certificate file and paste it below the final -----END CERTIFICATE----- line.
5. Delete metadata in between -----END CERTIFICATE----- and -----BEGIN CERTIFICATE----- lines, so the formatting is roughly as follows:

```
-----BEGIN CERTIFICATE-----
{cert}
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
{cert}
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
{Zscaler root cert}
-----END CERTIFICATE-----
```