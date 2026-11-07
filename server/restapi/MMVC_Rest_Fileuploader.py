import json
import os
import logging
from typing import Union
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi import UploadFile, File, Form

from restapi.mods.FileUploader import upload_file, concat_file_chunks
from voice_changer.VoiceChangerManager import VoiceChangerManager

from const import MODEL_DIR, UPLOAD_DIR
from voice_changer.utils.LoadModelParams import LoadModelParamFile, LoadModelParams


os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)


class MMVC_Rest_Fileuploader:
    def __init__(self, voiceChangerManager: VoiceChangerManager):
        self.voiceChangerManager = voiceChangerManager
        self.router = APIRouter()
        self.router.add_api_route("/info", self.get_info, methods=["GET"])
        self.router.add_api_route("/performance", self.get_performance, methods=["GET"])
        self.router.add_api_route("/upload_file", self.post_upload_file, methods=["POST"])
        self.router.add_api_route("/concat_uploaded_file", self.post_concat_uploaded_file, methods=["POST"])
        self.router.add_api_route("/update_settings", self.post_update_settings, methods=["POST"])
        self.router.add_api_route("/load_model", self.post_load_model, methods=["POST"])
        self.router.add_api_route("/load_model_if_empty", self.post_load_model_if_empty, methods=["POST"])
        self.router.add_api_route("/onnx", self.get_onnx, methods=["GET"])
        self.router.add_api_route("/merge_model", self.post_merge_models, methods=["POST"])
        self.router.add_api_route("/update_model_default", self.post_update_model_default, methods=["POST"])
        self.router.add_api_route("/update_model_info", self.post_update_model_info, methods=["POST"])
        self.router.add_api_route("/upload_model_assets", self.post_upload_model_assets, methods=["POST"])

    def post_upload_file(self, file: UploadFile = File(...), filename: str = Form(...)):
        try:
            res = upload_file(UPLOAD_DIR, file, filename)
            json_compatible_item_data = jsonable_encoder(res)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_upload_file ex:", e)

    def post_concat_uploaded_file(self, filename: str = Form(...), filenameChunkNum: int = Form(...)):
        try:
            res = concat_file_chunks(UPLOAD_DIR, filename, filenameChunkNum, UPLOAD_DIR)
            json_compatible_item_data = jsonable_encoder(res)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_concat_uploaded_file ex:", e)

    def get_info(self):
        try:
            info = self.voiceChangerManager.get_info()
            info["clientCapabilities"] = {"safeModelRegistration": True, "audioEpoch": True}
            model_dir = self.voiceChangerManager.params.model_dir
            info["occupiedModelSlots"] = sorted(int(entry.name) for entry in os.scandir(model_dir)
                if entry.name.isdecimal() and 0 <= int(entry.name) < 500) if os.path.isdir(model_dir) else []
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] get_info ex:", e)

    def get_performance(self):
        try:
            info = self.voiceChangerManager.get_performance()
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] get_performance ex:", e)

    def post_update_settings(self, key: str = Form(...), val: Union[int, str, float] = Form(...)):
        try:
            print("[Voice Changer] update configuration:", key, val)
            info = self.voiceChangerManager.update_settings(key, val)
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_update_settings ex:", e)
            import traceback
            traceback.print_exc()

    def post_load_model(
        self,
        slot: int = Form(...),
        isHalf: bool = Form(...),
        params: str = Form(...),
    ):
        try:
            paramDict = json.loads(params)
            print("paramDict", paramDict)
            loadModelparams = LoadModelParams(**paramDict)
            loadModelparams.files = [LoadModelParamFile(**x) for x in paramDict["files"]]
            # print("paramDict", loadModelparams)

            info = self.voiceChangerManager.loadModel(loadModelparams)
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_load_model ex:", e)
            import traceback
            traceback.print_exc()
            
    def post_load_model_if_empty(self, slot: int = Form(...), isHalf: bool = Form(...), params: str = Form(...)):
        try:
            values = json.loads(params)
            load_params = LoadModelParams(**values)
            load_params.files = [LoadModelParamFile(**value) for value in values["files"]]
            if load_params.slot != slot:
                raise ValueError("Slot fields do not match")
            self.voiceChangerManager.loadModel(load_params, require_empty=True)
            return {"status": "OK"}
        except FileExistsError:
            return JSONResponse(status_code=409, content={"error": {
                "code": "slot_occupied", "reason": "The slot already contains files. They have been preserved."}})
        except (ValueError, TypeError, KeyError) as error:
            return JSONResponse(status_code=422, content={"error": {
                "code": "invalid_resource", "reason": str(error)}})
        except Exception:
            logging.getLogger(__name__).exception("Safe model registration failed")
            return JSONResponse(status_code=422, content={"error": {
                "code": "model_load_failed", "reason": "The uploaded model could not be registered. Partial files have been preserved."}})

    def get_onnx(self):
        try:
            info = self.voiceChangerManager.export2onnx()
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] get_onnx ex:", e)
            import traceback
            traceback.print_exc()

    def post_merge_models(self, request: str = Form(...)):
        try:
            print(request)
            info = self.voiceChangerManager.merge_models(request)
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_merge_models ex:", e)
            import traceback
            traceback.print_exc()

    def post_update_model_default(self):
        try:
            info = self.voiceChangerManager.update_model_default()
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_update_model_default ex:", e)
            import traceback
            traceback.print_exc()

    def post_update_model_info(self, newData: str = Form(...)):
        try:
            info = self.voiceChangerManager.update_model_info(newData)
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_update_model_info ex:", e)

    def post_upload_model_assets(self, params: str = Form(...)):
        try:
            info = self.voiceChangerManager.upload_model_assets(params)
            json_compatible_item_data = jsonable_encoder(info)
            return JSONResponse(content=json_compatible_item_data)
        except Exception as e:
            print("[Voice Changer] post_update_model_info ex:", e)
