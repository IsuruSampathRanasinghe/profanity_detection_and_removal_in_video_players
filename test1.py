import torch
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger.info("GPU: %s", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU")