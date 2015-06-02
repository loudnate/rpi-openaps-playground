"""
Model generator for GlucoDyn event history
"""
from datetime import datetime

class GlucoDynEventHistory(object):
    def __init__(self, pump_history, zero_datetime=None):
        self.uevent = []
        self.raw = pump_history
        self.zero_datetime = zero_datetime or datetime.now()
        
        for event in pump_history:
            try:
                decoded = getattr(self, "decode_{}".format(event["_type"]))(event)
            except AttributeError:
                pass
            else:
                if decoded is not None:
                    self.uevent.append(decoded)
    
    def decode_Bolus(self, event):
        return {
            "etype": "bolus",
            "time": int(round((event["timestamp"] - self.zero_datetime).total_seconds())),
            "units": event["amount"]
        }
        
    def decode_BolusWizard(self, event):
        return {
            "etype": "carb",
            "time": int(round((event["timestamp"] - self.zero_datetime).total_seconds())),
            "grams": event["carb_input"]
        }
    
    decode_JournalEntryMealMarker = decode_BolusWizard