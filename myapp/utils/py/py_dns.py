# pip install dnspython
import dns.resolver
from urllib.parse import urlparse
import logging

def get_ips_by_domain(domain):
    # 通过域名查找ip列表
    ips = []
    all = dns.resolver.query(domain)
    for ip in all:
        ips.append(ip.address)
    return ips


def validate_ip(ip_str):
    sep = ip_str.split('.')
    if len(sep) != 4:
        return False
    for i,x in enumerate(sep):
        try:
            int_x = int(x)
            if int_x < 0 or int_x > 255:
                return False
        except ValueError as e:
            return False
    return True

def extract_domain_from_url(url):
    parsed_uri = urlparse(url)
    return parsed_uri.hostname


def resolve_urls_from_domain(url):
    # 通过url获取域名下面的所有的ip
    try:
        parsed_uri = urlparse(url)
        domain = parsed_uri.hostname
        port = parsed_uri.port
        ips = get_ips_by_domain(domain)
        urls = []

        for ip in ips:
            urls.append("http://%s:%s%s"%(ip, port, parsed_uri.path))
        return urls
    except Exception as e:
        print(e)
        return [url]


if __name__ == "__main__":
    url = "http://www.baidu.com:8080/reset"
    print(resolve_urls_from_domain(url))