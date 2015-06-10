import random
import os
import shutil
import sqlite3


def FlipBit(valToInject, numBitsToInject, bitToInject):
    """
    Flip the bitToInject of the binary representation of valToInject and
    return the new value.
    """
    if bitToInject >= numBitsToInject or bitToInject < 0:
        raise Exception(
            'CheckpointInjection:FlipBit(): invalid bitToInject: '+str(bitToInject) +
            ' for numBitsToInject: '+str(numBitsToInject))
    valToInject = int(valToInject, base=0)
    binaryList = list(str(bin(valToInject))[2:].zfill(numBitsToInject))
    binaryList[numBitsToInject-1-bitToInject] = (
        '1' if binaryList[numBitsToInject-1-bitToInject] == '0' else '0')
    injectedVal = int(''.join(binaryList), 2)
    injectedVal = hex(injectedVal).rstrip('L')
    return injectedVal


def ChooseTarget(selectedTargets, targets):
    """
    Given a list of targets, randomly choose one and return it.
    If no list of targets is given, choose from all available targets.
    Random selection takes into account the number of bits each target contains.
    """
    targetToInject = None
    targetList = []
    totalBits = 0
    for target in targets:
        if selectedTargets is None or target in selectedTargets:
            bits = targets[target]['totalBits']
            targetList.append((target, bits))
            totalBits += bits
    randomBit = random.randrange(totalBits)
    bitSum = 0
    for target in targetList:
        bitSum += target[1]
        if randomBit < bitSum:
            targetToInject = target[0]
            break
    else:
        raise Exception('CheckpointInjection:ChooseTarget(): Error choosing injection target')
    if 'count' in targets[targetToInject]:
        targetIndex = random.randrange(targets[targetToInject]['count'])
        targetToInject += ':'+str(targetIndex)
    return targetToInject


def ChooseRegister(target, targets):
    """
    Randomly choose a register from the target and return it.
    Random selection takes into account the number of bits each register
    contains.
    """
    if ':' in target:
        target = target.split(':')[0]
    registers = targets[target]['registers']
    registerToInject = None
    registerList = []
    totalBits = 0
    for register in registers:
        bits = registers[register]['totalBits']
        registerList.append((register, bits))
        totalBits += bits
    randomBit = random.randrange(totalBits)
    bitSum = 0
    for register in registerList:
        bitSum += register[1]
        if randomBit < bitSum:
            registerToInject = register[0]
            break
    else:
        raise Exception('CheckpointInjection:ChooseRegister(): Error choosing register for target: '+target)
    return registerToInject


def InjectRegister(goldCheckpoint, injectedCheckpoint, register, target, board, targets, previousInjectionData=None):
    """
    Creates config file for injectedCheckpoint with an injected value for the
    register of the target in the goldCheckpoint and return the injection
    information.
    """
    if previousInjectionData is None:
        # create injectionData
        injectionData = {}
        injectionData['register'] = register
        if ':' in target:
            targetIndex = target.split(':')[1]
            target = target.split(':')[0]
            configObject = 'DUT_'+board+targets[target]['OBJECT']+'['+targetIndex+']'
        else:
            targetIndex = 'N/A'
            configObject = 'DUT_'+board+targets[target]['OBJECT']
        injectionData['targetIndex'] = targetIndex
        configType = targets[target]['TYPE']
        injectionData['configType'] = configType
        injectionData['target'] = target
        injectionData['configObject'] = configObject
        if 'count' in targets[target]['registers'][register]:
            registerIndex = []
            for dimension in targets[target]['registers'][register]['count']:
                registerIndex.append(random.randrange(dimension))
        else:
            registerIndex = None
        injectionData['registerIndex'] = 'N/A' if registerIndex is None else registerIndex
        # choose bitToInject and TLB fieldToInject
        if 'isTLB' in targets[target]['registers'][register] and targets[target]['registers'][register]['isTLB']:
            fields = targets[target]['registers'][register]['fields']
            fieldToInject = 'N/A'
            fieldsList = []
            totalBits = 0
            for field in fields:
                bits = fields[field]['bits']
                fieldsList.append((field, bits))
                totalBits += bits
            randomBit = random.randrange(totalBits)
            bitSum = 0
            for field in fieldsList:
                bitSum += field[1]
                if randomBit < bitSum:
                    fieldToInject = field[0]
                    break
            else:
                raise Exception('CheckpointInjection:InjectRegister(): Error choosing TLB field to inject')
            injectionData['field'] = fieldToInject
            if 'split' in fields[fieldToInject] and fields[fieldToInject]['split']:
                totalBits = fields[fieldToInject]['bitsH'] + fields[fieldToInject]['bitsL']
                randomBit = random.randrange(totalBits)
                if randomBit < fields[fieldToInject]['bitsL']:
                    registerIndex[-1] = fields[fieldToInject]['indexL']
                    startBitIndex = fields[fieldToInject]['bitIndiciesL'][0]
                    endBitIndex = fields[fieldToInject]['bitIndiciesL'][1]
                else:
                    registerIndex[-1] = fields[fieldToInject]['indexH']
                    startBitIndex = fields[fieldToInject]['bitIndiciesH'][0]
                    endBitIndex = fields[fieldToInject]['bitIndiciesH'][1]
            else:
                registerIndex[-1] = fields[fieldToInject]['index']
                startBitIndex = fields[fieldToInject]['bitIndicies'][0]
                endBitIndex = fields[fieldToInject]['bitIndicies'][1]
            numBitsToInject = 32
            bitToInject = random.randrange(startBitIndex, endBitIndex+1)
        else:
            if 'bits' in targets[target]['registers'][register]:
                numBitsToInject = targets[target]['registers'][register]['bits']
            else:
                numBitsToInject = 32
            bitToInject = random.randrange(numBitsToInject)
            if 'adjustBit' in targets[target]['registers'][register]:
                bitToInject = targets[target]['registers'][register]['adjustBit'][bitToInject]
            if 'actualBits' in targets[target]['registers'][register]:
                numBitsToInject = targets[target]['registers'][register]['actualBits']
            if 'fields' in targets[target]['registers'][register]:
                for fieldName, fieldBounds in targets[target]['registers'][register]['fields'].iteritems():
                    if bitToInject in xrange(fieldBounds[0], fieldBounds[1]+1):
                        fieldToInject = fieldName
                        break
                else:
                    raise Exception('CheckpointInjection:InjectRegister(): Error finding register field name')
                injectionData['field'] = fieldToInject
            else:
                injectionData['field'] = 'N/A'
        injectionData['bit'] = bitToInject
    else:
        # use previous injection data
        configObject = previousInjectionData['configObject']
        configType = previousInjectionData['configType']
        registerIndex = previousInjectionData['registerIndex']
        if registerIndex == 'N/A':
            registerIndex = None
        injectionData = {}
        injectedValue = previousInjectionData['injectedValue']
    # perform checkpoint injection
    with open(goldCheckpoint+'/config', 'r') as goldConfig, open(injectedCheckpoint+'/config', 'w') as injectedConfig:
        currentLine = goldConfig.readline()
        injectedConfig.write(currentLine)
        # write out configuration data until injection target found
        while 'OBJECT '+configObject+' TYPE '+configType+' {' not in currentLine:
            currentLine = goldConfig.readline()
            injectedConfig.write(currentLine)
            if currentLine == '':
                raise Exception(
                    'CheckpointInjection:InjectRegister(): Could not find '+configObject +
                    ' in '+goldCheckpoint+'/config')
        # find target register
        while '\t'+register+': ' not in currentLine:
            currentLine = goldConfig.readline()
            if 'OBJECT' in currentLine:
                raise Exception(
                    'CheckpointInjection:InjectRegister(): Could not find '+register+' in '+configObject +
                    ' in '+goldCheckpoint+'/config')
            elif '\t'+register+': ' not in currentLine:
                injectedConfig.write(currentLine)
        # inject register value
        if registerIndex is None:
            goldValue = currentLine.split(':')[1].strip()
            if previousInjectionData is None:
                injectedValue = FlipBit(goldValue, numBitsToInject, bitToInject)
            injectedConfig.write('\t'+register+': '+injectedValue+'\n')
        # parse register list
        else:
            registerBuffer = currentLine.strip()
            if len(registerIndex) == 1:
                while ')' not in currentLine:
                    currentLine = goldConfig.readline()
                    registerBuffer += currentLine.strip()
                registerBuffer = registerBuffer.replace(' ', '')
                registerList = registerBuffer[registerBuffer.index('(')+1:registerBuffer.index(')')].split(',')
                goldValue = registerList[registerIndex[0]]
                if previousInjectionData is None:
                    injectedValue = FlipBit(goldValue, numBitsToInject, bitToInject)
                registerList[registerIndex[0]] = injectedValue
                injectedConfig.write('\t'+register+': (')
                lineToWrite = ''
                for index in xrange(len(registerList)):
                    if index == len(registerList)-1:
                        if lineToWrite == '':
                            injectedConfig.write(registerList[index]+')\n')
                        else:
                            injectedConfig.write(lineToWrite+', '+registerList[index]+')\n')
                    else:
                        if len(lineToWrite+registerList[index]+', ') > 80:
                            injectedConfig.write(lineToWrite+',\n\t'+'       ')
                            lineToWrite = registerList[index]
                        elif lineToWrite == '':
                            lineToWrite += registerList[index]
                        else:
                            lineToWrite += ', '+registerList[index]
            elif len(registerIndex) == 2:
                while '))' not in currentLine:
                    currentLine = goldConfig.readline()
                    registerBuffer += currentLine.strip()
                registerBuffer = registerBuffer.replace(' ', '')
                registerList = registerBuffer[registerBuffer.index('((')+2:registerBuffer.index('))')].split('),(')
                for registerIndex1 in xrange(len(registerList)):
                    registerList[registerIndex1] = registerList[registerIndex1].split(',')
                goldValue = registerList[registerIndex[0]][registerIndex[1]]
                if previousInjectionData is None:
                    injectedValue = FlipBit(goldValue, numBitsToInject, bitToInject)
                registerList[registerIndex[0]][registerIndex[1]] = injectedValue
                injectedConfig.write('\t'+register+': ((')
                for index1 in xrange(len(registerList)):
                    for index2 in xrange(len(registerList[index1])):
                        if index2 != len(registerList[index1])-1:
                            injectedConfig.write(registerList[index1][index2]+', ')
                        elif index1 != len(registerList)-1:
                            injectedConfig.write(registerList[index1][index2]+'),\n\t       (')
                        else:
                            injectedConfig.write(registerList[index1][index2]+'))\n')
            elif len(registerIndex) == 3:
                while ')))' not in currentLine:
                    currentLine = goldConfig.readline()
                    registerBuffer += currentLine.strip()
                registerBuffer = registerBuffer.replace(' ', '')
                registerList = registerBuffer[registerBuffer.index('(((')+3:registerBuffer.index(')))')].split(')),((')
                for index1 in xrange(len(registerList)):
                    registerList[index1] = registerList[index1].split('),(')
                    for index2 in xrange(len(registerList[index1])):
                        registerList[index1][index2] = registerList[index1][index2].split(',')
                goldValue = registerList[registerIndex[0]][registerIndex[1]][registerIndex[2]]
                if previousInjectionData is None:
                    injectedValue = FlipBit(goldValue, numBitsToInject, bitToInject)
                registerList[registerIndex[0]][registerIndex[1]][registerIndex[2]] = injectedValue
                injectedConfig.write('\t'+register+': (((')
                for index1 in xrange(len(registerList)):
                    for index2 in xrange(len(registerList[index1])):
                        for index3 in xrange(len(registerList[index1][index2])):
                            if index3 != len(registerList[index1][index2])-1:
                                injectedConfig.write(
                                    registerList[index1][index2][index3]+', ')
                            elif index2 != len(registerList[index1])-1:
                                injectedConfig.write(
                                    registerList[index1][index2][index3]+'),\n\t        (')
                            elif index1 != len(registerList)-1:
                                injectedConfig.write(
                                    registerList[index1][index2][index3]+')),\n\t       ((')
                            else:
                                injectedConfig.write(
                                    registerList[index1][index2][index3]+')))\n')
            else:
                raise Exception(
                    'CheckpointInjection:InjectRegister(): Too many dimensions for register '+register +
                    ' in target: '+target)
        injectionData['goldValue'] = goldValue
        injectionData['injectedValue'] = injectedValue
        # write out remaining configuration data
        while currentLine != '':
            currentLine = goldConfig.readline()
            injectedConfig.write(currentLine)
    return injectionData


def InjectCheckpoint(injectionNumber, board, selectedTargets, num_checkpoints):
    """
    Create a new injected checkpoint (only performing injection on the
    selectedTargets if provided) and return the path of the injected checkpoint.
    """
    if board == 'p2020rdb':
        from simics_targets import P2020 as targets
    elif board == 'a9x4':
        from simics_targets import A9 as targets
    # verify selected targets exist
    if selectedTargets is not None:
        for target in selectedTargets:
            if target not in targets:
                raise Exception('CheckpointInjection:InjectCheckpoint(): invalid injection target: '+target)
    # choose a checkpoint for injection
    checkpointList = os.listdir('simics-workspace/gold-checkpoints')
    for checkpoint in checkpointList:
        if '.ckpt' not in checkpoint:
            checkpointList.remove(checkpoint)
    checkpointList.remove('checkpoint-'+str(num_checkpoints-1)+'.ckpt')
    goldCheckpoint = 'simics-workspace/gold-checkpoints/'+checkpointList[random.randrange(len(checkpointList))]
    # create injected checkpoint directory
    if not(os.path.exists('simics-workspace/injected-checkpoints')):
        os.mkdir('simics-workspace/injected-checkpoints')
    checkpointNumber = int(goldCheckpoint.split('/')[-1][goldCheckpoint.split('/')[-1].index('-') +
                           1:goldCheckpoint.split('/')[-1].index('.ckpt')])
    injectedCheckpoint = ('simics-workspace/injected-checkpoints/' +
                          str(injectionNumber)+'_'+'checkpoint-'+str(checkpointNumber)+'.ckpt')
    os.mkdir(injectedCheckpoint)
    # copy gold checkpoint files
    checkpointFiles = os.listdir(goldCheckpoint)
    checkpointFiles.remove('config')
    # checkpointFiles.remove('DebugInfo.txt')
    for checkpointFile in checkpointFiles:
        shutil.copyfile(goldCheckpoint+'/'+checkpointFile, injectedCheckpoint+'/'+checkpointFile)
    # choose injection target
    target = ChooseTarget(selectedTargets, targets)
    register = ChooseRegister(target, targets)
    # perform fault injection
    injectionData = InjectRegister(goldCheckpoint, injectedCheckpoint, register, target, board, targets)
    # log injection data
    injectionData['injectionNumber'] = injectionNumber
    injectionData['checkpointNumber'] = checkpointNumber
    # with open(goldCheckpoint+'/DebugInfo.txt', 'r') as debugInfo:
    #     injectionData['goldDebugInfo'] = debugInfo.read()
    sql_db = sqlite3.connect('django-logging/db.sqlite3')
    sql = sql_db.cursor()
    registerIndex = ''
    for index in injectionData['registerIndex']:
        registerIndex += str(index)+':'
    registerIndex = registerIndex[:-1]
    sql.execute(
        'INSERT INTO drseus_logging_simics_injection ' +
        '(injection_number,register,bit,gold_value,injected_value,' +
        'checkpoint_number,target_index,target,config_object,register_index,' +
        'field) VALUES (?,?,?,?,?,?,?,?,?,?,?)',
        (
            injectionData['injectionNumber'], injectionData['register'],
            injectionData['bit'], injectionData['goldValue'],
            injectionData['injectedValue'], injectionData['checkpointNumber'],
            injectionData['targetIndex'], injectionData['target'],
            injectionData['configObject'], registerIndex, injectionData['field']
        )
    )
    sql_db.commit()
    sql_db.close()
    return injectedCheckpoint.replace('simics-workspace/', '')
