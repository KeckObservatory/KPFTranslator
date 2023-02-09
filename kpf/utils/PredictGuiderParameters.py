description = '''
'''

# Engineering OBs (not consistent)
# Jmag, Gain
# 4.37, low
# 2.14, low
# 4.45, low
# 4.29, low
# 6.13, low
# 4.88, low
# 4.48, low
# 5.93, low
# 3.3, low
# 4.48, low
# 9, medium
# 10, medium
# 7.5, low
# 2.4, low
# 8.4, high

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
