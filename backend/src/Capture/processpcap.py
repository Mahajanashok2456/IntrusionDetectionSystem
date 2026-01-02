from scapy.all import *
from collections import defaultdict
import math
import config

def get_service_name(port):
    services = {
        80: 'http', 
        443: 'http_443', 
        22: 'ssh', 
        25: 'smtp',
        53: 'domain',
        21: 'ftp',
        23: 'telnet',
        110: 'pop_3',
        143: 'imap4',
        512: 'exec',
        513: 'login',
        514: 'shell',
        3306: 'sql_net',
        3389: 'ms-term-server'
    }
    return services.get(port, 'other')

def determine_nslkdd_flag(tcp_flags):
    """Map TCP flags to NSL-KDD flag categories"""
    if 'SYN' in tcp_flags and 'FIN' in tcp_flags:
        return 'SF'
    elif 'SYN' in tcp_flags and 'ACK' not in tcp_flags:
        return 'S0'
    elif 'RST' in tcp_flags:
        return 'RSTR'
    return 'OTH'

def get_tcp_flags(packets):
    flags = set()
    for p in packets:
        if TCP in p:
            if p[TCP].flags & 0x01: flags.add('FIN')
            if p[TCP].flags & 0x02: flags.add('SYN')
            if p[TCP].flags & 0x04: flags.add('RST')
            if p[TCP].flags & 0x08: flags.add('PSH')
            if p[TCP].flags & 0x10: flags.add('ACK')
            if p[TCP].flags & 0x20: flags.add('URG')
    return determine_nslkdd_flag(flags)

def count_failed_logins(payloads):
    """Count failed login attempts in payloads"""
    patterns = [b'login failed', b'authentication failed', b'incorrect password']
    return sum(1 for p in payloads if any(pat in p.lower() for pat in patterns))

def group_packets_into_connections(packets, timeout=120):
    """Group packets into connections based on 5-tuple with timeout"""
    connections = defaultdict(list)
    
    for pkt in packets:
        if IP in pkt and TCP in pkt:
            key = (pkt[IP].src, pkt[TCP].sport,
                   pkt[IP].dst, pkt[TCP].dport,
                   pkt[IP].proto)
            connections[key].append(pkt)
    
    return list(connections.values())

# Feature Extraction Functions
def get_basic_features(packets):
    timestamps = [p.time for p in packets]
    return {
        'duration': max(timestamps) - min(timestamps) if len(timestamps) > 1 else 0,
        'protocol_type': 'tcp' if packets[0][IP].proto == 6 else 'udp',
        'service': get_service_name(packets[0][TCP].dport),
        'flag': get_tcp_flags(packets),
        'src_bytes': sum(len(p) for p in packets if p[IP].src == packets[0][IP].src),
        'dst_bytes': sum(len(p) for p in packets if p[IP].dst == packets[0][IP].dst),
        'land': 1 if (packets[0][IP].src == packets[0][IP].dst and 
                     packets[0][TCP].sport == packets[0][TCP].dport) else 0,
        'wrong_fragment': sum(1 for p in packets if IP in p and p[IP].frag != 0),
        'urgent': sum(p[TCP].urgptr for p in packets if TCP in p and hasattr(p[TCP], 'urgptr'))
    }

def get_content_features(packets):
    payloads = [p[TCP].payload.load for p in packets if TCP in p and hasattr(p[TCP].payload, 'load')]
    return {
        'hot': sum(1 for p in payloads if len(p) > 100),
        'num_failed_logins': count_failed_logins(payloads),
        'logged_in': 1 if any(b'login successful' in p.lower() for p in payloads) else 0,
        'num_compromised': 0,  
        'root_shell': 1 if any(b'root#' in p.lower() for p in payloads) else 0,
        'su_attempted': 1 if any(b'su -' in p.lower() for p in payloads) else 0,
        'num_root': sum(1 for p in payloads if b'root:' in p.lower()),
        'num_file_creations': sum(1 for p in payloads if b'mkdir' in p.lower() or b'touch' in p.lower()),
        'num_shells': sum(1 for p in payloads if b'sh -c' in p.lower()),
        'num_access_files': sum(1 for p in payloads if b'/etc/passwd' in p.lower()),
        'num_outbound_cmds': 0,  # Typically 0 in modern traffic
        'is_host_login': 1 if packets[0][TCP].dport == 513 else 0,
        'is_guest_login': 1 if packets[0][TCP].dport == 514 else 0
    }

def get_time_features(all_connections, current_conn, time_window=2):
    window_start = current_conn[-1].time - time_window
    src_ip = current_conn[0][IP].src
    
    related_conns = [c for c in all_connections 
                    if c[0][IP].src == src_ip and
                    c[-1].time >= window_start]
    
    total = len(related_conns)
    srv_count = sum(1 for c in related_conns 
                   if c[0][TCP].dport == current_conn[0][TCP].dport)
    
    return {
        'count': total,
        'srv_count': srv_count,
        'serror_rate': calc_error_rate(related_conns, 'RST'),
        'srv_serror_rate': calc_srv_error_rate(related_conns, current_conn[0][TCP].dport, 'RST'),
        'rerror_rate': calc_error_rate(related_conns, 'REJ'),
        'srv_rerror_rate': calc_srv_error_rate(related_conns, current_conn[0][TCP].dport, 'REJ'),
        'same_srv_rate': srv_count/total if total > 0 else 0,
        'diff_srv_rate': (total - srv_count)/total if total > 0 else 0,
        'srv_diff_host_rate': len({c[0][IP].dst for c in related_conns})/total if total > 0 else 0
    }

def get_host_features(all_connections, current_conn):
    dst_ip = current_conn[0][IP].dst
    dst_port = current_conn[0][TCP].dport
    
    dst_host_conns = [c for c in all_connections if c[0][IP].dst == dst_ip]
    total = len(dst_host_conns)
    srv_count = sum(1 for c in dst_host_conns if c[0][TCP].dport == dst_port)
    
    return {
        'dst_host_count': total,
        'dst_host_srv_count': srv_count,
        'dst_host_same_srv_rate': srv_count/total if total > 0 else 0,
        'dst_host_diff_srv_rate': (total - srv_count)/total if total > 0 else 0,
        'dst_host_same_src_port_rate': len({c[0][TCP].sport for c in dst_host_conns})/total if total > 0 else 0,
        'dst_host_srv_diff_host_rate': len({c[0][IP].src for c in dst_host_conns})/total if total > 0 else 0,
        'dst_host_serror_rate': calc_error_rate(dst_host_conns, 'RST'),
        'dst_host_srv_serror_rate': calc_srv_error_rate(dst_host_conns, dst_port, 'RST'),
        'dst_host_rerror_rate': calc_error_rate(dst_host_conns, 'REJ'),
        'dst_host_srv_rerror_rate': calc_srv_error_rate(dst_host_conns, dst_port, 'REJ')
    }

def calc_error_rate(connections, flag_type):
    total = len(connections)
    if total == 0: return 0
    errors = sum(1 for c in connections if flag_type in get_tcp_flags(c))
    return errors / total

def calc_srv_error_rate(connections, port, flag_type):
    srv_conns = [c for c in connections if c[0][TCP].dport == port]
    return calc_error_rate(srv_conns, flag_type)

# Main Processing
def process_pcap(pcap_file):
    packets = rdpcap(pcap_file)
    all_connections = group_packets_into_connections(packets)
    
    nslkdd_features = []
    for conn in all_connections:
        features = {}
        features.update(get_basic_features(conn))
        features.update(get_content_features(conn))
        features.update(get_time_features(all_connections, conn))
        features.update(get_host_features(all_connections, conn))
        nslkdd_features.append(features)
    
    return nslkdd_features

def save_to_arff(features, output_file):
    FEATURE_ORDER = [
        'duration', 'protocol_type', 'service', 'flag', 'src_bytes', 'dst_bytes',
        'land', 'wrong_fragment', 'urgent', 'hot', 'num_failed_logins', 'logged_in',
        'num_compromised', 'root_shell', 'su_attempted', 'num_root', 'num_file_creations',
        'num_shells', 'num_access_files', 'num_outbound_cmds', 'is_host_login',
        'is_guest_login', 'count', 'srv_count', 'serror_rate', 'srv_serror_rate',
        'rerror_rate', 'srv_rerror_rate', 'same_srv_rate', 'diff_srv_rate',
        'srv_diff_host_rate', 'dst_host_count', 'dst_host_srv_count',
        'dst_host_same_srv_rate', 'dst_host_diff_srv_rate', 'dst_host_same_src_port_rate',
        'dst_host_srv_diff_host_rate', 'dst_host_serror_rate', 'dst_host_srv_serror_rate',
        'dst_host_rerror_rate', 'dst_host_srv_rerror_rate'
    ]
    
    with open(output_file, 'w') as f:
        f.write('@RELATION NSL_KDD\n')
        # Write attribute definitions
        f.write('@ATTRIBUTE duration numeric\n')
        f.write('@ATTRIBUTE protocol_type {tcp,udp,icmp}\n')
        f.write('@ATTRIBUTE service {aol,auth,bgp,courier,csnet_ns,ctf,daytime,discard,domain,domain_u,echo,eco_i,ecr_i,efs,exec,finger,ftp,ftp_data,gopher,harvest,hostnames,http,http_2784,http_443,http_8001,imap4,IRC,iso_tsap,klogin,kshell,ldap,link,login,mtp,name,netbios_dgm,netbios_ns,netbios_ssn,netstat,nnsp,nntp,ntp_u,other,pm_dump,pop_2,pop_3,printer,private,red_i,remote_job,rje,shell,smtp,sql_net,ssh,sunrpc,supdup,systat,telnet,tftp_u,tim_i,time,urh_i,urp_i,uucp,uucp_path,vmnet,whois,X11,Z39_50}\n')
        f.write('@ATTRIBUTE flag {OTH,REJ,RSTO,RSTOS0,RSTR,S0,S1,S2,S3,SF,SH}\n')
        # ... continue with all other attributes
        
        f.write('@DATA\n')
        for feat in features:
            f.write(','.join(str(feat.get(k, '?')) for k in FEATURE_ORDER) + '\n')

# # Usage
# if __name__ == "__main__":
#     features = process_pcap(config.PCAP_SAVE_PATH)
#     save_to_arff(features, "nslkdd_features.arff")
#     import pandas as pd
#     df = pd.DataFrame(features)
#     df.to_csv("the_features.csv", index=False)
