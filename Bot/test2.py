

    def deal_msg(self, msg):
        xml = msg.content
        root = ET.fromstring(xml) 
        datas = dict(root.find('.//emoji').items())
        cdnurl = datas["cdnurl"].replace('&amp;', '&')
        if not filename:
            filename = msg.id
        save_path = f"{self.emotion_save_path}{os.sep}{filename}.gif"
        with open(save_path, 'wb') as f:
            f.write(self.download_file(cdnurl))
    
    def download_file(self, url, retry=0):
        if retry > 2:
            return
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183"
        }
        try:
            resp = requests.get(url, headers=headers, timeout=6)
        except:
            traceback.print_exc()
            time.sleep(2)
            return self.download_file(url, retry+1)
        return resp.content