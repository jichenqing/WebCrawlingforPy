from threading import Thread

from utils.download import download
from utils import get_logger
from scraper import scraper
from scraper import save_to_file
import time
from threading import Lock



class Worker(Thread):
    def __init__(self, worker_id, config, frontier):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        super().__init__(daemon=True)



        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                #with Lock():
                save_to_file()
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            if resp.error is None and resp.raw_response is not None:
                scraped_urls = scraper(tbd_url, resp)
                if scraped_urls:
                    if len(scraped_urls)!=0:
                        for scraped_url in scraped_urls:
                            self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)    
            time.sleep(self.config.time_delay)
                
           
