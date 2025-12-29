import sys
import os
import json

sys.path.append(os.path.join(os.getcwd(), 'src'))

from generate_json_test_nb import patterns
from model.region import RegionModel
from converter.validator import region_validator

print(f"Testing {len(patterns)} patterns...")

for p in patterns:
    print(f"Testing pattern: {p['name']}")
    try:
        region_json = p['json']
        # Simulate Pydantic validation
        region_model = RegionModel.model_validate(region_json)
        
        # Run functional validator
        is_valid = region_validator(region_model)
        
        if not is_valid:
            print(f"❌ Pattern '{p['name']}' FAILED validation!")
            # Retrigger validator to capture logging if possible (or just rely on previous run if it printed to stdout/err which it usually does via logging)
            # But the logger uses `logging.getLogger`. It might not print to stdout unless configured.
            # I will configure logging to verify.
        else:
            print(f"✅ Pattern '{p['name']}' passed.")
            
    except Exception as e:
        print(f"❌ Pattern '{p['name']}' FAILED with exception: {e}")
        import traceback
        traceback.print_exc()

import logging
logging.basicConfig(level=logging.ERROR)
