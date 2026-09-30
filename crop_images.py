"""Pre-crop all Stitch images for the Vercel static dashboard."""
from PIL import Image
import os

stitch_dir = "stitch_google_photos_retrieval_discovery_engine/stitch_google_photos_retrieval_discovery_engine"
out_dir = "dashboard/images"

crops = {
    "overview": ("google_photos_retrieval_discovery_overview", 380),
    "dataset": ("google_photos_research_dataset", 370),
    "feedback": ("google_photos_user_feedback", 180),
    "behavior": ("google_photos_search_behavior", 178),
    "failures": ("where_google_photos_retrieval_breaks", 350),
    "opportunities": ("evidence_product_opportunities", 395),
}

for name, (folder, crop_left) in crops.items():
    img_path = os.path.join(stitch_dir, folder, "screen.png")
    img = Image.open(img_path)
    w, h = img.size
    cropped = img.crop((crop_left, 0, w, h))
    out_path = os.path.join(out_dir, f"{name}.png")
    cropped.save(out_path, optimize=True)
    print(f"Saved {out_path}: {cropped.width}x{cropped.height}")

print("Done!")
