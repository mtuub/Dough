from django.db import models
import uuid
import json

class BaseModel(models.Model):
    uuid = models.UUIDField(default=uuid.uuid4)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    is_disabled = models.BooleanField(default=False)

    class Meta:
        abstract = True


class InternalFileObject(BaseModel):
    name = models.TextField(default="")
    type = models.CharField(max_length=255, default="")     # image, video, audio
    local_path = models.TextField(default="")
    hosted_url = models.TextField(default="")

    class Meta:
        db_table = 'file'

    @property
    def location(self):
        return self.local_path if self.local_path else self.hosted_url


class User(BaseModel):
    name = models.CharField(max_length=255, default="")
    email = models.CharField(max_length=255)
    password = models.TextField(default=None, null=True)
    type = models.CharField(max_length=50, default="user")
    third_party_id = models.CharField(max_length=255, default=None, null=True)

    class Meta:
        db_table = 'user'


class Project(BaseModel):
    name = models.CharField(max_length=255, default="")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)

    class Meta:
        db_table = 'project'


class AIModel(BaseModel):
    name = models.CharField(max_length=255, default="")
    user = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True)      # incase this is a user specific custom model
    version = models.CharField(max_length=255, default="", blank=True)
    replicate_model_id = models.CharField(max_length=255, default="", blank=True)      # for models which were custom created
    replicate_url = models.TextField(default="", blank=True)
    diffusers_url = models.TextField(default="", blank=True)    # for downloading and running models offline
    category = models.CharField(max_length=255,default="", blank=True)     # Lora, Dreambooth..
    training_image_list = models.TextField(default="", blank=True)      # contains an array of uuid of file objects

    class Meta:
        db_table = 'ai_model'
    

class InferenceLog(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    model = models.ForeignKey(AIModel, on_delete=models.DO_NOTHING, null=True)
    input_params = models.TextField(default="", blank=True)
    output_details = models.TextField(default="", blank=True)
    total_inference_time = models.IntegerField(default=0)

    class Meta:
        db_table = 'inference_log'


class AIModelParamMap(BaseModel):
    model = models.ForeignKey(AIModel, on_delete=models.DO_NOTHING, null=True)
    standard_param_key = models.CharField(max_length=255, blank=True)
    model_param_key = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'model_param_map'


class Timing(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True)
    model = models.ForeignKey(AIModel, on_delete=models.DO_NOTHING, null=True)
    source_image = models.ForeignKey(InternalFileObject, related_name="source_image", on_delete=models.DO_NOTHING, null=True)
    interpolated_clip = models.ForeignKey(InternalFileObject, related_name="interpolated_clip", on_delete=models.DO_NOTHING, null=True)
    timed_clip = models.ForeignKey(InternalFileObject, related_name="timed_clip", on_delete=models.DO_NOTHING, null=True)
    mask = models.ForeignKey(InternalFileObject, related_name="mask", on_delete=models.DO_NOTHING, null=True)
    canny_image = models.ForeignKey(InternalFileObject, related_name="canny_image", on_delete=models.DO_NOTHING, null=True)
    preview_video = models.ForeignKey(InternalFileObject, related_name="preview_video", on_delete=models.DO_NOTHING, null=True)
    custom_model_id_list = models.TextField(default=None, null=True, blank=True)    
    frame_time = models.FloatField(default=None, null=True)
    frame_number = models.IntegerField(default=None, null=True)
    primary_image = models.IntegerField(default=None, null=True)   # variant number that is currently selected (among alternative images) NONE if none is present
    alternative_images = models.TextField(default=None, null=True)
    custom_pipeline = models.CharField(max_length=255, default="", blank=True)
    prompt = models.TextField(default='', blank=True)
    negative_prompt = models.TextField(default="", blank=Tue)
    guidance_scale = models.FloatField(default=7.5)
    seed = models.IntegerField(default=0)
    num_inteference_steps = models.IntegerField(default=50)
    strength = models.FloatField(default=4)
    notes = models.TextField(default="", blank=True)
    adapter_type = models.CharField(max_length=255, default="", blank=True)
    clip_duration = models.FloatField(default=None, null=True)     # clip duration of the timed_clip
    animation_style = models.CharField(max_length=255, default=None, null=True)
    interpolation_steps = models.IntegerField(default=0)
    low_threshold = models.FloatField(default=0)
    high_threshold = models.FloatField(default=0)
    aux_frame_index = models.IntegerField(default=0)    # TODO: udpate this

    class Meta:
        db_table = 'frame_timing'

    @property
    def alternative_images_list(self):
        image_id_list = json.loads(self.alternative_images) if self.alternative_images else []
        return InternalFileObject.objects.filter(id__in=image_id_list, is_disabled=False).all()
    
    @property
    def primary_variant_location(self):
        if not len(self.alternative_images_list):
            return ""
        else:                         
            return self.alternative_images_list[self.primary_image].location if self.primary_image < len(self.alternative_images_list) else ""
    
    # index starts with 0
    @property
    def aux_frame_index(self):
        project_frames = Timing.objects.filter(project=self.project, is_disabled=False).all()
        return project_frames.objects.filter(id__lt=self.id).count()
    
    # gives the next entry in the project timings
    @property
    def next_timing(self):
        next_timing = Timing.objects.filter(project=self.project, id__gt=self.id, is_disabled=False).order_by('id').first()
        return next_timing
    
    @property
    def prev_timing(self):
        prev_timing = Timing.objects.filter(project=self.project, id__lt=self.id, is_disabled=False).order_by('id').first()
        return prev_timing


class AppSetting(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    replicate_key = models.CharField(max_length=255, default="", blank=True)
    aws_access_key = models.CharField(max_length=255, default="", blank=True)
    stability_key = models.CharField(max_length=255, default="", blank=True)
    previous_project = models.CharField(max_length=255, default="", blank=True)
    replicate_user_name = models.CharField(max_length=255, default="", blank=True)
    welcome_state = models.IntegerField(default=0)

    class Meta:
        db_table = 'app_setting'

    def save(self, *args, **kwargs):
        from utils.encryption import Encryptor
        encryptor = Encryptor()

        new_access_key = not self.id or ('aws_access_key' in kwargs and kwargs['aws_access_key'] != self.aws_access_key)
        new_replicate_key = not self.id or ('replicate_key' in kwargs and kwargs['replicate_key'] != self.replicate_key)
        new_stability_key = not self.id or ('stability_key' in kwargs and kwargs['stability_key'] != self.stability_key)

        if new_access_key:
            encrypted_access_key = encryptor.encrypt(self.aws_access_key)
            self.aws_access_key = encrypted_access_key
        
        if new_replicate_key:
            encrypted_replicate_key = encryptor.encrypt(self.replicate_key)
            self.replicate_key = encrypted_replicate_key

        if new_stability_key:
            encrypted_stability_key = encryptor.encrypt(self.stability_key)
            self.stability_key = encrypted_stability_key

        super(AppSetting, self).save(*args, **kwargs)

    @property
    def aws_access_key_decrypted(self):
        from utils.encryption import Encryptor
        encryptor = Encryptor()
        return encryptor.decrypt(self.aws_access_key)
    
    @property
    def replicate_key_decrypted(self):
        from utils.encryption import Encryptor
        encryptor = Encryptor()
        return encryptor.decrypt(self.replicate_key)
    
    @property
    def stability_key_decrypted(self):
        from utils.encryption import Encryptor
        encryptor = Encryptor()
        return encryptor.decrypt(self.stability_key)



class Setting(BaseModel):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    default_model = models.ForeignKey(AIModel, on_delete=models.DO_NOTHING, null=True)
    audio = models.ForeignKey(InternalFileObject, related_name="audio", on_delete=models.DO_NOTHING, null=True)
    input_video = models.ForeignKey(InternalFileObject, related_name="input_video", on_delete=models.DO_NOTHING, null=True)
    default_prompt = models.TextField(default="")
    default_strength = models.FloatField(default=0.7)
    default_custom_pipeline = models.CharField(max_length=255, default="", blank=True)
    input_type = models.CharField(max_length=255)   # video, image, audio
    extraction_type = models.CharField(max_length=255)   # Extract manually
    width = models.IntegerField(default=512)
    height = models.IntegerField(default=512)
    default_negative_prompt = models.TextField(default="")
    default_guidance_scale = models.FloatField(default=7.5)
    default_seed = models.IntegerField(default=0)
    default_num_inference_steps = models.IntegerField(default=50)
    default_stage = models.CharField(max_length=255)    # extracted_key_frames
    default_custom_model_id_list = models.TextField(default=None, null=True, blank=True)
    default_adapter_type = models.CharField(max_length=255, default="", blank=True)
    guidance_type = models.CharField(max_length=255)   # "Drawing", "Images", "Video"
    default_animation_style = models.CharField(max_length=255)  # "Interpolation", "Direct Morphing"
    default_low_threshold = models.FloatField(default=0)
    default_high_threshold = models.FloatField(default=0)

    class Meta:
        db_table = 'setting'


