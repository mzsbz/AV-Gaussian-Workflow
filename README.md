# Setup

{dataset_name} = {dataset_location}_{dataset_type}_{dataset_date}-{dataset_no}

- put data in ../_dataset/{dataset_name}/_source/original

- If 360 video
    - run `extract_360video.py`
        - output front: ../_dataset/{dataset_name}/_source/extracted/front
        - output back : ../_dataset/{dataset_name}/_source/extracted/back
        - symlink front: ../_dataset/{dataset_name}/_source/colmap_images/front
        - symlink back : ../_dataset/{dataset_name}/_source/colmap_images/back
    - run `colmap_sfm_fisheye.py`
        - output: ../_dataset/{dataset_name}/colmap_runs/{data_variant}
    - run `run_3dgrut_train.py`
        - output: ../_dataset/{dataset_name}/3dgrut_runs/{data_variant}/{data_variant}-{DDMM_HHMMSS}
- If 360 photos
    - run `extract_360photo.py`
        - output front: ../_dataset/{dataset_name}/_source/extracted/front
        - output back : ../_dataset/{dataset_name}/_source/extracted/back
    - run `downsample_images.py`
        - output front: ../_dataset/{dataset_name}/_source/colmap_images/front_{downsample_factor}
        - output back : ../_dataset/{dataset_name}/_source/colmap_images/back_{downsample_factor}
    - run `colmap_sfm_fisheye.py`
        - output: ../_dataset/{dataset_name}/colmap_runs/{data_variant}
    - run `run_3dgrut_train.py`
        - output: ../_dataset/{dataset_name}/3dgrut_runs/{data_variant}/{data_variant}-{DDMM_HHMMSS}
- If photos
    - run `downsample_images.py`
        - output: ../_dataset/{dataset_name}/_source/colmap_images/images_{downsample_factor}
    - run `colmap_sfm_pinhole.py`
        - output: ../_dataset/{dataset_name}/colmap_runs/{data_variant}
    - run `run_3dgrut_train.py`
        - output: ../_dataset/{dataset_name}/3dgrut_runs/{data_variant}/{data_variant}-{DDMM_HHMMSS}