import header

class Resize:
    """현 이미지크기 비율을 조절하여 이미지 및 json 데이터를 저장한다.
    
    .. note::

        각 이미지에 대해 이미지 비율을 조절하며 해당 비율에 따른 annotations에 관련된 내용들을 변경합니다.(annotations, area, bbox)
        이미지에 대한 정보(width, height) 또한 변경합니다.
    """
    
    def make_dir(self, file_path, is_remove):
        try:
            if is_remove:
                shutil.rmtree(file_path)
        except Exception as ex:
            pass
        try:
            os.makedirs(file_path)
        except Exception as ex:
            pass
        
    def load_image(self, load_path, file_name):
        path_name = f"{load_path}/{file_name}"
        
        image_array = np.fromfile(path_name, np.uint8)
        result = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
        return result

    def save_image(self, data, save_path, file_name):
        self.make_dir(save_path,is_remove=False)
        path_name = f"{save_path}/{file_name}"
        path_name = path_name.replace(".tiff", ".jpg")
        
        extension = os.path.splitext(path_name)[1]
        result, encoded_img = cv2.imencode(extension, data)
        
        if result: 
            with open(path_name, mode="w+b") as f: 
                encoded_img.tofile(f)

    def load_json(self, load_path, file_name):
        path_name = f"{load_path}/{file_name}"
        with open(path_name, "r", encoding="UTF-8") as json_file:
            json_data = json.load(json_file)
        return json_data

    def save_json(self, data, save_path, file_name):
        self.make_dir(save_path,is_remove=False)
        path_name = f"{save_path}/{file_name}"
        with open(path_name, "w", encoding="UTF-8") as json_file:
            json.dump(data, json_file, indent=4, separators=(',', ': '), ensure_ascii=False)

    def resize(self, data, options):
        width = options["width"]
        height = options["height"]
        fx = options["fx"]
        fy = options["fy"]
        
        result = cv2.resize(data, dsize=(width, height), fx=fx, fy=fy, interpolation=cv2.INTER_CUBIC)
        return result

    def _area(self, area, rate):
        result = int(area * rate)
        return result

    def _bbox(self, bbox, width, height):
        bbox_array = np.round_([bbox[0]*width,bbox[1]*height,bbox[2]*width,bbox[3]*height],0)
        result = bbox_array.tolist()
        return result

    def _segmentation(self, segmentation, width, height):
        result = []
        for seg in segmentation:
            seg_array = np.array(seg, dtype=np.float64)
            seg_array[::2] *= width
            seg_array[1::2] *= height
            seg_array = np.round_(seg_array, 0)  
            result.append(seg_array.tolist())
        return result

    def resize_json(self, load_json_path,file_name):
        json_data = self.load_json(load_json_path,file_name)
        
        images = json_data["images"]
        categories = json_data["categories"]
        annotations = json_data["annotations"]
        info = json_data["info"]
        metainfo = json_data["metainfo"]
        
        resize_json_data = {
            "images":[],
            "categories":categories,
            "annotations":[],
            "info":info,
            "metainfo":metainfo
        }
        rate = 2048/2024
        
        for image in images:
            copy_image = copy.copy(image)
            
            copy_image["width"] = 2048
            copy_image["height"] = 2048
            resize_json_data["images"].append(copy_image)
        
        for annotation in annotations:
            copy_annotation = copy.copy(annotation)
            
            copy_annotation["bbox"] = self._bbox(annotation["bbox"],rate,rate)
            copy_annotation["segmentation"] = self._segmentation(annotation["segmentation"],rate,rate)
            copy_annotation["area"] = self._area(annotation["area"],rate)
            
            resize_json_data["annotations"].append(copy_annotation)
        
        return resize_json_data
        
    def resize_image(self, load_image_path,file_name):
        image_data = self.load_image(load_image_path,file_name)
        size = 2048
        
        resize_options = {
            "width":size,
            "height":size,
            "fx":0,
            "fy":0
        }
        resize_image_data = self.resize(image_data,resize_options)
        
        return resize_image_data

    def load_file_list(self, ends_with, file_path):
        
        full_result = []
        path_result = []
        name_result = []

        file_names = os.listdir(file_path)
        
        for file_name in file_names:
            if file_name.endswith(ends_with):
                full_file_name = os.path.join(file_path, file_name)
                full_file_name = full_file_name.replace("\\","/")
                full_result.append(full_file_name)
                path_result.append(file_path)
                name_result.append(file_name)

        return full_result, path_result, name_result

    def run(self, options):
        """해당 함수는 다음과 같이 정의됩니다.
        각각의 데이터 경로에 대한 정보를 불러와 해당 정보에 대한 image 및 json을 변경합니다.

        Args:
            options (dict) : 입력값을 정의합니다.
        
        Return: 
            None

        Raise:
            fileio - 파일 입출력에 관한 에러

        options의 구성은 다음과 같이 정의 됩니다.
        
        .. code-block:: JSON

            "options": {
                "load_image_path": "image 파일 경로",
                "load_json_path": "json 파일 경로",
                "save_image_path": "image 파일 저장",
                "save_json_path": "json 파일 저장",
                "file_name": "파일 명"
            }
        """
        
        load_image_path = options["load_image_path"]
        load_json_path = options["load_json_path"]
        save_image_path = options["save_image_path"]
        save_json_path = options["save_json_path"]
        
        # tiff 확장자 사용할경우 .jpg를 .tiff로 변경
        # _, _, image_names = self.load_file_list(".jpg",load_image_path)
        # 이미지 파일 변환이 필요 없을경우 주석처리
        # for name in image_names:
        #     resize_image_data = self.resize_image(load_image_path,f"{name}")
        #     self.save_image(resize_image_data, save_image_path,name)

        # json 파일 변환이 필요 없을경우 주석처리
        _, _, json_names = self.load_file_list(".json",load_json_path)
        
        for name in json_names:
            resize_json_data = self.resize_json(load_json_path,f"{name}")
            self.save_json(resize_json_data, save_json_path,f"{name}")
        
        
if __name__ == '__main__':
    resize_options ={
        "load_image_path":"./sample/image/PET",
        "load_json_path":"./sample/json/PET",
        "save_image_path":"./result/image/PET",
        "save_json_path":"./result/json/PET",
    }    
    resize = Resize()
    resize.run(options=resize_options)