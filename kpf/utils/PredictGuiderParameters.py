description = '''
'''

def predict_guider_parameters(Jmag):
    if Jmag < 5.0:
        guider_parameters = {'GuideCamGain': 'low',
                             'GuideFPS': 100}
    elif Jmag < 8.0:
        guider_parameters = {'GuideCamGain': 'medium',
                             'GuideFPS': 100}
    elif Jmag < 11.5:
        guider_parameters = {'GuideCamGain': 'high',
                             'GuideFPS': 100}
    elif Jmag < 12.5:
        guider_parameters = {'GuideCamGain': 'high',
                             'GuideFPS': 50}
    elif Jmag < 13.5:
        guider_parameters = {'GuideCamGain': 'high',
                             'GuideFPS': 20}
    else:
        guider_parameters = {'GuideCamGain': 'high',
                             'GuideFPS': 10}
    return guider_parameters


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=description)
    p.add_argument('Jmag', type=float,
                   help="The target J magnitude")
    args = p.parse_args()
    result = predict_guider_parameters(args.Jmag)
    print(result)
