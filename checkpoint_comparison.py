import sqlite3


def CompareCheckpoints(injection_number, checkpoint_number, board):
    """
    Compares the registers and memory of the monitored checkpoint to the
    goldCheckpoint and returns an incrementalResult dictionary.
    """


    CompareRegisters(
        gold_checkpoint, monitoredCheckpoint, board, targets)


def ParseRegisters(configFile, board, targets):
    """
    Retrieves all the register values of the targets specified in
    InjectionTargets for the specified checkpoint configFile and returns a
    dictionary with all the values.
    """
    registers = {}
    for target in targets:
        if target != 'TLB':
            if 'count' in targets[target]:
                count = targets[target]['count']
            else:
                count = 1
            for targetIndex in xrange(count):
                configObject = 'DUT_'+board+targets[target]['OBJECT']
                configType = targets[target]['TYPE']
                if count > 1:
                    configObject += '['+str(targetIndex)+']'
                if target == 'GPR':
                    targetKey = configObject + ':gprs'
                else:
                    targetKey = configObject
                registers[targetKey] = {}
                with open(configFile, 'r') as config:
                    currentLine = config.readline()
                    while 'OBJECT '+configObject+' TYPE '+configType+' {' not in currentLine:
                        currentLine = config.readline()
                        if currentLine == '':
                            raise Exception(
                                'ExecutionMonitoring:ParseRegisters(): could not find '+configObject+' in '+configFile)
                    currentLine = config.readline()
                    while 'OBJECT' not in currentLine and currentLine != '':
                        if ':' in currentLine:
                            currentItem = currentLine.split(':')[0].strip()
                            if currentItem in targets[target]['registers']:
                                if 'count' in targets[target]['registers'][currentItem]:
                                    dimensions = len(targets[target]['registers'][currentItem]['count'])
                                    registerBuffer = currentLine.strip()
                                    if dimensions == 1:
                                        while ')' not in currentLine:
                                            currentLine = config.readline()
                                            registerBuffer += currentLine.strip()
                                        registerBuffer = registerBuffer.replace(' ', '')
                                        registerList = registerBuffer[
                                            registerBuffer.index('(')+1:registerBuffer.index(')')].split(',')
                                    elif dimensions == 2:
                                        while '))' not in currentLine:
                                            currentLine = config.readline()
                                            registerBuffer += currentLine.strip()
                                        registerBuffer = registerBuffer.replace(' ', '')
                                        registerList = registerBuffer[
                                            registerBuffer.index('((')+2:registerBuffer.index('))')].split('),(')
                                        for index in xrange(len(registerList)):
                                            registerList[index] = registerList[index].split(',')
                                    else:
                                        raise Exception(
                                            'ExecutionMonitoring:ParseRegisters(): Too many dimensions for register ' +
                                            ' in target: '+target)
                                    registers[targetKey][currentItem] = registerList
                                else:
                                    currentValue = currentLine.split(':')[1].strip()
                                    registers[targetKey][currentItem] = currentValue
                        currentLine = config.readline()
                if len(registers[targetKey]) != len(targets[target]['registers']):
                    print registers[targetKey]
                    print targets[target]['registers']
                    missingRegisters = []
                    for register in targets[target]['registers']:
                        if register not in registers[targetKey]:
                            missingRegisters.append(register)
                    raise Exception(
                        'ExecutionMonitoring:ParseRegisters(): Could not find the following registers for ' +
                        configObject+': '+str(missingRegisters))
    return registers


def CompareRegisters(injection_number, monitored_checkpoint_number,
                     goldCheckpoint, monitoredCheckpoint, board):
    """
    Compares the register values of the monitoredCheckpoint to the
    goldCheckpoint and returns the differences in dictionary as well as the
    total number of differences.
    """
    if board == 'p2020rdb':
        from simics_targets import P2020 as targets
    elif board == 'a9x4':
        from simics_targets import A9 as targets
    goldRegisters = ParseRegisters(goldCheckpoint+'/config', board, targets)
    monitoredRegisters = ParseRegisters(monitoredCheckpoint+'/config', board, targets)
    sql_db = sqlite3.connect('django-logging/db.sqlite3')
    sql = sql_db.cursor()
    for target in targets:
        if target != 'TLB':
            if 'count' in targets[target]:
                targetCount = targets[target]['count']
            else:
                targetCount = 1
            for targetIndex in xrange(targetCount):
                configObject = 'DUT_'+board+targets[target]['OBJECT']
                if targetCount > 1:
                    configObject += '['+str(targetIndex)+']'
                if target == 'GPR':
                    targetKey = configObject + ':gprs'
                else:
                    targetKey = configObject
                for register in targets[target]['registers']:
                    if 'count' in targets[target]['registers'][register]:
                        registerCount = targets[target]['registers'][register]['count']
                    else:
                        registerCount = ()
                    if len(registerCount) == 0:
                        if monitoredRegisters[targetKey][register] != goldRegisters[targetKey][register]:
                            sql.execute(
                                'INSERT INTO ' +
                                'drseus_logging_simics_register_diff ' +
                                '(injection_number,' +
                                'monitored_checkpoint_number,config_object,' +
                                'register,gold_value,monitored_value) ' +
                                'VALUES (?,?,?,?,?,?)', (
                                    injection_number,
                                    monitored_checkpoint_number, targetKey,
                                    register,
                                    goldRegisters[targetKey][register],
                                    monitoredRegisters[targetKey][register]
                                )
                            )
                    elif len(registerCount) == 1:
                        for index1 in xrange(registerCount[0]):
                            if monitoredRegisters[targetKey][register][index1] != \
                                    goldRegisters[targetKey][register][index1]:
                                sql.execute(
                                    'INSERT INTO ' +
                                    'drseus_logging_simics_register_diff ' +
                                    '(injection_number,' +
                                    'monitored_checkpoint_number,config_object,' +
                                    'register,gold_value,monitored_value) ' +
                                    'VALUES (?,?,?,?,?,?)', (
                                        injection_number,
                                        monitored_checkpoint_number, targetKey,
                                        register+':'+str(index1),
                                        goldRegisters[targetKey][register][index1],
                                        monitoredRegisters[targetKey][register][index1]
                                    )
                                )
                    elif len(registerCount) == 2:
                        for index1 in xrange(registerCount[0]):
                            for index2 in xrange(registerCount[1]):
                                if monitoredRegisters[targetKey][register][index1][index2] != \
                                        goldRegisters[targetKey][register][index1][index2]:
                                    sql.execute(
                                        'INSERT INTO ' +
                                        'drseus_logging_simics_register_diff ' +
                                        '(injection_number,' +
                                        'monitored_checkpoint_number,config_object,' +
                                        'register,gold_value,monitored_value) ' +
                                        'VALUES (?,?,?,?,?,?)', (
                                            injection_number,
                                            monitored_checkpoint_number, targetKey,
                                            register+':'+str(index1)+':'+str(index2),
                                            goldRegisters[targetKey][register][index1][index2],
                                            monitoredRegisters[targetKey][register][index1][index2]
                                        )
                                    )
                    else:
                        raise Exception(
                            'ExecutionMonitoring:CompareRegisters(): Too many dimensions for register '+register +
                            ' in target: '+target)
    sql_db.commit()
    sql_db.close()
