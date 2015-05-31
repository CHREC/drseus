import os
import re
import subprocess
import pickle
# from collections import OrderedDict


def CompareCheckpoints(
        goldCheckpoint, monitoredIncrementalCheckpoint, monitoredMergedCheckpoint=None,
        monitoredDebugInfo='', compareMemory=False, extractDiffBlocks=False):
    """
    Compares the registers and memory of the monitored checkpoint to the
    goldCheckpoint and returns an incrementalResult dictionary.
    """
    # with open(goldCheckpoint+'/DebugInfo.txt', 'r') as goldDebugInfoFile:
    #     goldDebugInfo = goldDebugInfoFile.read()
    numRegisterErrors, registerDiffs = CompareRegisters(
        goldCheckpoint, monitoredMergedCheckpoint if compareMemory else monitoredIncrementalCheckpoint)
    if compareMemory:
        changedMemoryBlocks = CompareMemoryContents(
            goldCheckpoint, monitoredIncrementalCheckpoint, monitoredMergedCheckpoint, extractDiffBlocks)
        numChangedMemoryBlocks = len(changedMemoryBlocks)
    else:
        changedMemoryBlocks = ['N/A', ]
        numChangedMemoryBlocks = 'N/A'
    incrementalResult = {
        'monitoredCheckpoint': monitoredIncrementalCheckpoint,
        'goldCheckpoint': goldCheckpoint,
        # 'goldDebugInfo': goldDebugInfo,
        # 'monitoredDebugInfo': monitoredDebugInfo,
        'registerDiffs': registerDiffs,
        'numRegisterErrors': numRegisterErrors,
        'changedMemoryBlocks': changedMemoryBlocks,
        'numChangedMemoryBlocks': numChangedMemoryBlocks
    }
    return incrementalResult


def ParseRegisters(configFile):
    """
    Retrieves all the register values of the targets specified in
    InjectionTargets for the specified checkpoint configFile and returns a
    dictionary with all the values.
    """
    with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
        campaignData = pickle.load(campaign_pickle)
    if campaignData['board'] == 'p2020rdb':
        from simics_targets import P2020 as targets
    elif campaignData['board'] == 'a9x4':
        from simics_targets import A9 as targets
    registers = {}
    for target in targets:
        if target != 'TLB':
            if 'count' in targets[target]:
                count = targets[target]['count']
            else:
                count = 1
            for targetIndex in xrange(count):
                configObject = 'DUT_'+campaignData['board']+targets[target]['OBJECT']
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


def CompareRegisters(goldCheckpoint, monitoredCheckpoint):
    """
    Compares the register values of the monitoredCheckpoint to the
    goldCheckpoint and returns the differences in dictionary as well as the
    total number of differences.
    """
    with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
        campaignData = pickle.load(campaign_pickle)
    if campaignData['board'] == 'p2020rdb':
        from simics_targets import P2020 as targets
    elif campaignData['board'] == 'a9x4':
        from simics_targets import A9 as targets
    goldRegisters = ParseRegisters(goldCheckpoint+'/config')
    monitoredRegisters = ParseRegisters(monitoredCheckpoint+'/config')
    registerErrors = 0
    registerDiffs = {}
    for target in targets:
        if target != 'TLB':
            if 'count' in targets[target]:
                targetCount = targets[target]['count']
            else:
                targetCount = 1
            for targetIndex in xrange(targetCount):
                configObject = 'DUT_'+campaignData['board']+targets[target]['OBJECT']
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
                            registerErrors += 1
                            if targetKey not in registerDiffs:
                                registerDiffs[targetKey] = {}  # OrderedDict()
                            registerDiffs[targetKey][register] = {
                                'goldValue': goldRegisters[targetKey][register],
                                'monitoredValue': monitoredRegisters[targetKey][register]}
                    elif len(registerCount) == 1:
                        for index1 in xrange(registerCount[0]):
                            if monitoredRegisters[targetKey][register][index1] != \
                                    goldRegisters[targetKey][register][index1]:
                                registerErrors += 1
                                if target == 'GPR':
                                    registerDiffKey = 'r'+str(index1)
                                else:
                                    registerDiffKey = register+':'+str(index1)
                                if targetKey not in registerDiffs:
                                    registerDiffs[targetKey] = {}  # OrderedDict()
                                if registerDiffKey not in registerDiffs[targetKey]:
                                    registerDiffs[targetKey][registerDiffKey] = {}
                                registerDiffs[targetKey][registerDiffKey] = {
                                    'goldValue': goldRegisters[targetKey][register][index1],
                                    'monitoredValue': monitoredRegisters[targetKey][register][index1]}
                    elif len(registerCount) == 2:
                        for index1 in xrange(registerCount[0]):
                            for index2 in xrange(registerCount[1]):
                                if monitoredRegisters[targetKey][register][index1][index2] != \
                                        goldRegisters[targetKey][register][index1][index2]:
                                    registerErrors += 1
                                    registerDiffKey = register+':'+str(index1)+':'+str(index2)
                                    if targetKey not in registerDiffs:
                                        registerDiffs[targetKey] = {}  # OrderedDict()
                                    if registerDiffKey not in registerDiffs[targetKey]:
                                        registerDiffs[targetKey][registerDiffKey] = {}
                                    registerDiffs[targetKey][registerDiffKey] = {
                                        'goldValue': goldRegisters[targetKey][register][index1][index2],
                                        'monitoredValue': monitoredRegisters[targetKey][register][index1][index2]}
                    else:
                        raise Exception(
                            'ExecutionMonitoring:CompareRegisters(): Too many dimensions for register '+register +
                            ' in target: '+target)
    return registerErrors, registerDiffs


def ParseContentMap(contentMap, blockSize):
    """
    Parse a contentMap created by the Simics craff utility and returns a list of
    the addresses of the image that contain data.
    """
    with open(contentMap, 'r') as contentMapFileObject:
        diffAddresses = []
        for line in contentMapFileObject:
            if 'empty' not in line:
                line = line.split()
                baseAddress = int(line[0], 16)
                offsets = [index for index, value in enumerate(line[1]) if value == 'D']
                for offset in offsets:
                    diffAddresses.append(baseAddress+offset*blockSize)
    return diffAddresses


def ExtractDiffBlocks(
        goldCheckpointRAM, monitoredCheckpointRAM, monitoredIncrementalCheckpoint, addressesToRead, blockSize):
    """
    Extract all of the blocks of size blockSize specified in addressesToRead of
    both the goldCheckpointRAM image and the monitoredCheckpointRAM image.
    """
    if len(addressesToRead) > 0:
        os.mkdir(monitoredIncrementalCheckpoint+'/MemoryBlocks')
        for address in addressesToRead:
            outputGoldBlock = (
                monitoredIncrementalCheckpoint+'/MemoryBlocks/'+hex(address)+'_Gold.raw')
            outputMonitoredBlock = (
                monitoredIncrementalCheckpoint+'/MemoryBlocks/'+hex(address)+'_Monitored.raw')
            os.system(
                './bin/craff '+goldCheckpointRAM+' --extract='+hex(address) +
                ' --extract-block-size='+str(blockSize)+' --output='+outputGoldBlock)
            os.system(
                './bin/craff '+monitoredCheckpointRAM+' --extract='+hex(address) +
                ' --extract-block-size='+str(blockSize)+' --output='+outputMonitoredBlock)


def CompareMemoryContents(goldCheckpoint, monitoredIncrementalCheckpoint, monitoredMergedCheckpoint, extractDiffBlocks):
    """
    Compare the memory contents of goldCheckpoint with monitoredMergedCheckpoint
    and return the list of blocks that do not match. If extractDiffBlocks is
    true then extract any blocks that do not match to
    monitoredIncrementalCheckpoint.
    """
    with open('campaign-data/campaign.pickle', 'r') as campaign_pickle:
        campaignData = pickle.load(campaign_pickle)
    goldCheckpointRAM = goldCheckpoint+'/DUT_'+campaignData['board']+'.soc.ram_image[0].craff'
    monitoredCheckpointRAM = monitoredMergedCheckpoint+'/DUT_'+campaignData['board']+'.soc.ram_image[0].craff'
    diffFile = monitoredCheckpointRAM+'.diff'
    diffContentMap = monitoredMergedCheckpoint+'/RAMdiff.contentmap'
    os.system('./bin/craff --diff '+goldCheckpointRAM+' '+monitoredCheckpointRAM+' --output='+diffFile)
    os.system('./bin/craff --content-map '+diffFile+' --output='+diffContentMap)
    craffOutput = subprocess.check_output('./bin/craff --info '+diffFile, shell=True)
    blockSize = int(re.findall(r'\d+', craffOutput.split('\n')[2])[1])
    changedMemoryBlocks = ParseContentMap(diffContentMap, blockSize)
    if extractDiffBlocks:
        ExtractDiffBlocks(
            goldCheckpointRAM, monitoredCheckpointRAM, monitoredIncrementalCheckpoint, changedMemoryBlocks, blockSize)
    changedMemoryBlocksHex = []
    for block in changedMemoryBlocks:
        changedMemoryBlocksHex.append(hex(block))
    return changedMemoryBlocksHex
