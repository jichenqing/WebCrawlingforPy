from bs4 import BeautifulSoup
import urllib.request
import urllib.robotparser
import re
from urllib.parse import urlparse
import sys
from collections import defaultdict
import requests
from urllib.error import HTTPError



unique=dict()
robotdic=dict()
commonword=defaultdict(int)
subdomain=defaultdict(int)

LongestPage =str()
LongestCount=0




def scraper(url, resp):
 
    
    links = extract_next_links(url, resp)
    if links is not None and len(links)!=0:
            
        #find valid links (text,http,within domains, useful status code)
        valid=[link for link in links if is_valid(link)]


        #exclude similar pages  
        fetch=[]
        for link1,link2 in zip(valid,valid[1:]):
            if "?" not in link1 :

                if checksimilar(link1,link2) is False:

                              
                    fetch.append(link1)
                    if "?" not in link2 :

                        fetch.append(link2)
                else:
                    if link1 in unique:
                        fetch.append(link1)
                
        return fetch

    else:
        return []



def checksimilar(link1,link2):

    global unique
    global regx

    
    
    if unique[link1] is None or len(unique[link1])==0:
        del unique[link1]
        return flag
                              
    if unique[link2] is None or len(unique[link2])==0:
        del unique [link2]
        return flag
    
    else:
        worddic1= unique[link1]
        worddic2= unique[link2]

            
        sharedic={k: worddic1[k] for k in worddic1 if k in worddic2 and worddic1[k] == worddic2[k]}

        if len(sharedic)/len(worddic1)>=0.75 or len(sharedic)/len(worddic2)>=0.75:
            return True
        else:
            return False




def save_to_file():

    global LongestCount
    global LongestPage
    global unique
    global commonword
    global subdomain


    
    with open('report.txt','w',encoding='utf-8') as file:
        
        # unique count
        
        file.write("Number of Unique Pages: "+str(len(unique))+"\n\n")


        # longest count
        
        for page in unique:
            
            if sum(unique[page].values())>LongestCount:
                
                LongestCount=sum(unique[page].values())
                LongestPage=page

        
        file.write("Longest Page: "+LongestPage+" "+str(LongestCount)+" words\n\n")


        # most common words

        file.write("50 Most Common Words: \n")

        i=0
        for url in unique:
            for word in unique[url]:
                commonword[word]+= 1
        
        for kk,vv in sorted(commonword.items(),key=lambda item:item[1],reverse=True):
            i+=1
            if i==51:
                break
            else:
                file.write(str(i)+": "+kk+", "+str(vv)+"\n")

                
        # subdomain + unique count
        file.write("\n\nSubdomains of .ics.uci.edu: \n")
        
        
        for link in unique:
            
            parsed=urlparse(link)

            if re.fullmatch(r"[^\..]+\.ics\.uci\.edu$", parsed.hostname):
                
                subdomain[parsed.hostname]+= 1
                

        for k,v in sorted(subdomain.items(),key=lambda item:item[0]):
            
            file.write("{}, {}\n".format(k,str(v))+"\n")

    



def hasrobot(parsed):
    
    

    global robotdic
    
   
    port=""
    if parsed.port:
        port=":"+str(parsed.port)

    roboturl=parsed.scheme + "://" + parsed.hostname + port + "/robots.txt"

    
    if parsed not in robotdic:
    
        try:
            rp=urllib.robotparser.RobotFileParser(roboturl)
            rp.read()
            robotdic[parsed]=rp
            return True
            
        
        except urllib.error.HTTPError:
            return False
        except urllib.error.URLError:
            return False
        
        except:
           
            return False
    else:
        return True
        


def extract_next_links(url, resp):
    global robotdic

    try:
        links=list()
        
        if is_valid(url) and 200<=resp.status<=202:


            if resp.raw_response is not None:
                
                soup = BeautifulSoup(resp.raw_response.content,'lxml')

                if soup.find_all('a') is not None:
                    if len(soup.find_all('a'))>=1:
                        for link in soup.find_all('a'):
                            if link.get('href') is not None:
                                if len(link.get('href'))>=1:

                                    link=link.get('href').split('#')[0]
                                    parsed=urlparse(url)
                               
                                    if hasrobot(parsed):
                                        if robotdic[parsed].can_fetch("IR S20 33337876",link):
                                
                                            links.append(link)
                                        
                                    else:
                                        links.append(link)

        return links
        
             
    except urllib.error.HTTPError:
        return []
    except urllib.error.URLError:
        return []
    
    except:
         
        print('extract'+sys.exc_info())
        return []
    

        

def is_valid(url):
    global robotdic
    
    try:
        flag=False
        
        global unique
           

        if url in unique:
            return flag
        
        req=requests.get(url,timeout=5,allow_redirects=True)

        if req.status_code<200 or req.status_code>202:
            return flag
        
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return flag

        if hasrobot(parsed):
            if robotdic[parsed].can_fetch("IR S20 33337876",url) is False:
                return flag

        
        
        '''
        is_chunked = req.headers.get('transfer-encoding', '') == 'chunked'
        
        if 'Conetent-Length' in req.headers:
            if not is_chuncked and int(req.headers['Conetnt-Length'])>MaxPageSize:
                return flag
        '''   
        if 'Content-Type' in req.headers:
            content_type=req.headers['Content-Type'].strip().split(';')[0].strip().lower()
            if content_type not in set(["text/plain","text/html", "application/xml","text/xml"]):
                return flag
            
        
                   
        
        if( ".ics.uci.edu"in parsed.hostname\
        or ".cs.uci.edu"in parsed.hostname\
        or ".informatics.uci.edu"in parsed.hostname\
        or  ".stat.uci.edu"in parsed.hostname\
        or ("today.uci.edu" in parsed.hostname\
        and  "department/information_computer_sciences"in parsed.path.lower())\
        and not re.search(
                r"\.(misc|degrees|css|js|bmp|gif|jpe?g|ico|css|field|no"
                + r"|policies|sao|computing|sites|all|themes|module|profiles"
                + r"|png|tiff?|mid|mp2|mp3|mp4|jpg"
                + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
                + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
                + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
                + r"|epub|dll|cnf|tgz|sha1"
                + r"|thmx|mso|arff|rtf|jar|csv"
                + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())\
        and not re.search(r"\/(photo|images)\/.*$",parsed.path.lower())):

            flag=True

            f=open("stopwords.txt",'r')
            stopwords=f.read().rstrip()
            f.close()

            
            unique[url]=dict()

            
            soup=BeautifulSoup(req.content,'lxml')
            text=soup.stripped_strings
            
                
            for string in text:
                string=re.findall(r'[A-Za-z]{2,}', string)
                for word in string:
                    word=word.lower()
                    if word not in stopwords:
                        unique[url][word]= unique[url].get(word, 0) + 1
            if unique[url] is None or len(unique[url])==0: 
                del unique[url]
                flag=False

                                       
        return flag

    
    except urllib.error.HTTPError:
        return False
    except urllib.error.URLError:
        return False
    except requests.exceptions.Timeout:
        return False
    except requests.exceptions.ConnectionError:
        return False
    except requests.exceptions.InvalidSchema:
        return False
    except requests.exceptions.MissingSchema:
        return False
    except:
        print(sys.exc_info())
        return False
        
