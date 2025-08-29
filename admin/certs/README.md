↩️ [Back to repository overview](../../README.md)

↩️ [Back to admin](../README.md)

## Creating custom certificate chains for use on the SOA network
Self-signed certificate errors can occur when SSL is used to verify connections made over HTTPS between the SOA network and an external endpoint.
Tools / libraries used to make connections may offer the ability to specify a custom certification file to verify the connection.
Using `openssl s_client` to retrieve the broken certificate chain from a problematic external endpoint and adding the Zscaler root certificate to the chain is one way to create the custom certification file. 

### Getting OpenSSL for Windows
FireDaemon provides binary distributions of OpenSSL for Microsoft Windows that can be installed as an executable (.exe). This is the easiest way to get up and running with OpenSSL. [Link here](https://kb.firedaemon.com/support/solutions/articles/4000121705#Windows-Installer)

### Using OpenSSL CLI to retrieve a certificate chain
[Documentation](https://docs.openssl.org/1.0.2/man1/s_client/#description)

***Examples***

`openssl s_client -connect=github.com:443 -showcerts`

`openssl s_client -connect=services.sentinel-hub.com:443 -showcerts`

`openssl s_client -connect=maps.matsugov.us:443 -showcerts`

`openssl s_client -connect anaconda.org:443 -showcerts`

`openssl s_client -connect pypi.org:443 -showcerts`

`openssl s_client -connect "ftp.wildfire.gov:1021" -starttls ftp -showcerts`

### Getting the Zscaler root certificate
Download "Windows Zscaler Root CA Certificate" from [SOA OIT](https://oit-int.alaska.gov/security/zscaler)

### Creating a custom .pem file
1. Open a blank file in an editor like Notepad++
2. Copy the output of a `openssl s_client -connect=<connection-endpoint>:443 -showcerts` command and paste it into the file
3. Delete content below the final -----END CERTIFICATE----- line
4. Copy content from the Zscaler root certificate file and paste it below the final -----END CERTIFICATE----- line
5. Delete metadata in between -----END CERTIFICATE----- and -----BEGIN CERTIFICATE----- lines, so formatting is as follows:

```
-----BEGIN CERTIFICATE-----
<cert>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<cert>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<cert>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<cert>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<cert>
-----END CERTIFICATE-----
-----BEGIN CERTIFICATE-----
<Zscaler root cert>
-----END CERTIFICATE-----
```
