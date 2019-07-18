import argparse
from dlgo.httpfrontend.server import get_web_app

parser = argparse.ArgumentParser()
parser.add_argument('-a', '--agent')
args = parser.parse_args()

agent_name = args.agent

if agent_name == "predict":
    
    from dlgo.agent.predict import DeepLearningAgent
    from dlgo.encoders.oneplane import OnePlaneEncoder
    from keras.models import load_model
    
    encoder = OnePlaneEncoder(19)
    model = load_model("../datasets/dlgo/checkpoints/small_model_epoch_5.h5")
    web_app = get_web_app({'predict': DeepLearningAgent(model, encoder)})

else:
    from dlgo.agent.naive import RandomBot
    web_app = get_web_app({'random': RandomBot()})

web_app.run()