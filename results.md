YJP-Lvl04_250828 [Insta360 x4]

    ## Run 01
    - Colmap Full Res: 59.159 mins
    - 3DGRUT Half Res: 30000 n_step, 60 n_epochs, 586.19s, 51.18 it/s
        - Mean PSNR : 6.847
        - Mean SSIM : 0.378
        - Mean LPIPS: 0.724
        - Std PSNR  : 0.000
    - 3DGRUT Full Res: 30000 n_step, 60 n_epochs, 2197.81s, 13.65 it/s

    No noticeable difference running 3DGRUT with half res vs full res.

    ## Run 02----------
    - Colmap Half Res: 50.743 mins
    -

YJP-Lvl04_250828_DSLR

    ## Run fullset_quarterres
    - Colmap 1/4 [1752 x 1168] Res: 1.430 mins
    - 3DGRUT 1/4 [1752 x 1168] Res: 30000 n_step, 60 n_epochs, 790.40s, 37.96 it/s [test/01-2808_165633]
        - Mean PSNR : 28.211
        - Mean SSIM : 0.886
        - Mean LPIPS: 0.275
        - Std PSNR  : 3.361
    - 3DGRUT 1/4 [1752 x 1168] Res: 100000 n_step, 60 n_epochs, 2914.70s, 34.31 it/s [test/01-2808_172229]

    Better quality then Insta360 x4 capture but double the capture time.
    No noticeable difference between 30,000 and 100,000 steps while taking 3.68x longer

    ## Run oddset_quarterres
    - Colmap 1/4 [1752 x 1168] Res: 0.528 mins
    - 3DGRUT 1/4 [1752 x 1168] Res: 30000 n_step, 60 n_epochs, 775.80s, 38.67 it/s
        - Mean PSNR : 25.590
        - Mean SSIM : 0.843
        - Mean LPIPS: 0.318
        - Std PSNR  : 3.656

    No noticeable difference with oddset vs fullset dataset. 
    Impercepitbly lower quality for slightly faster total processing time.
