from model_adapter import classify_emotion

tests = [
    ('I have so much work to do and deadlines are approaching!', 'stress'),
    ('This situation is making me so uncomfortable and on edge', 'tension'),
    ('That is absolutely revolting and disgusting', 'disgust'),
    ('I cannot wait for the results tomorrow!', 'anticipation'),
]

for msg, expected in tests:
    print(f'\n{expected.upper()} test:')
    print(f'Message: "{msg}"')
    result = classify_emotion(msg)
    dominant = max(result, key=result.get)
    print(f'Dominant: {dominant} ({result[dominant]:.2f})')
    print(f'All emotions: {result}')
