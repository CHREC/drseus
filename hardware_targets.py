from targets import calculate_target_bits

devices = {
    'a9': {
        'CP': {
            'registers': {
                'MIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'r'
                },
                'CTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'r'
                },
                'TCMTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'r'
                },
                'TLBTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 3,
                    'access': 'r'
                },
                'MPIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 5,
                    'access': 'r'
                },
                'REVIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 6,
                    'access': 'r'
                },
                'ID_PFR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'r'
                },
                'ID_PFR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'r'
                },
                'ID_DFR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 2,
                    'access': 'r'
                },
                'ID_AFR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 3,
                    'access': 'r'
                },
                'ID_MMFR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 4,
                    'access': 'r'
                },
                'ID_MMFR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 5,
                    'access': 'r'
                },
                'ID_MMFR2': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 6,
                    'access': 'r'
                },
                'ID_MMFR3': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 1,
                    'Op2': 7,
                    'access': 'r'
                },
                'ID_ISAR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 2,
                    'Op2': 0,
                    'access': 'r'
                },
                'ID_ISAR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 2,
                    'Op2': 1,
                    'access': 'r'
                },
                'ID_ISAR2': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 2,
                    'Op2': 2,
                    'access': 'r'
                },
                'ID_ISAR3': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 2,
                    'Op2': 3,
                    'access': 'r'
                },
                'ID_ISAR4': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 0,
                    'CRm': 2,
                    'Op2': 4,
                    'access': 'r'
                },
                'CCSIDR': {
                    'CP': 15,
                    'Op1': 1,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'r'
                },
                'CLIDR': {
                    'CP': 15,
                    'Op1': 1,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'r'
                },
                'AIDR': {
                    'CP': 15,
                    'Op1': 1,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 7,
                    'access': 'r'
                },
                'CSSELR': {
                    'CP': 15,
                    'Op1': 2,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'SCTLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'ACTLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                'CPACR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                },
                'SCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'rw'
                },
                'SDER': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'rw'
                },
                'NSACR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 2,
                    'access': 'rw'
                },
                'VCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 1,
                    'CRm': 1,
                    'Op2': 3,
                    'access': 'rw'
                },
                'TTBR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'TTBR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                'TTBCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                },
                'DACR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 3,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'DFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 5,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'IFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 5,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                'ADFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 5,
                    'CRm': 1,
                    'Op2': 0,
                    'access': ''
                },
                'AIFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 5,
                    'CRm': 1,
                    'Op2': 1,
                    'access': ''
                },
                'DFAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 6,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'IFAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 6,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                },
                'Reserved0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'w'
                },
                'Reserved1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'w'
                },
                'Reserved2': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'w'
                },
                'Reserved3': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 3,
                    'access': 'w'
                },
                'NOP': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 0,
                    'Op2': 4,
                    'access': 'w'
                },
                'ICIALLUIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'w'
                },
                'BPIALLIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 1,
                    'Op2': 6,
                    'access': 'w'
                },
                'Reserved4': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 1,
                    'Op2': 7,
                    'access': 'w'
                },
                'PAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 4,
                    'Op2': 0,
                    'access': 'rw'
                },
                'ICIALLU': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 0,
                    'access': 'w'
                },
                'ICIMVAU': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 1,
                    'access': 'w'
                },
                'Reserved5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 2,
                    'access': 'w'
                },
                'Reserved6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 3,
                    'access': 'w'
                },
                'ISB': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 4,
                    'access': 'w'
                },
                'BPIALL': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 5,
                    'Op2': 6,
                    'access': 'w'
                },
                'DCIMVAC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 6,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCISW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 6,
                    'Op2': 2,
                    'access': 'w'
                },
                'V2PCWPR0': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 0,
                    'access': 'w'
                },
                'V2PCWPR1': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 1,
                    'access': 'w'
                },
                'V2PCWPR2': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 2,
                    'access': 'w'
                },
                'V2PCWPR3': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 3,
                    'access': 'w'
                },
                'V2PCWPR4': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 4,
                    'access': 'w'
                },
                'V2PCWPR5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 5,
                    'access': 'w'
                },
                'V2PCWPR6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 6,
                    'access': 'w'
                },
                'V2PCWPR7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 8,
                    'Op2': 7,
                    'access': 'w'
                },
                'DCCVAC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCCSW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 2,
                    'access': 'w'
                },
                'DSB': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 4,
                    'access': 'w'
                },
                'DMB': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 10,
                    'Op2': 5,
                    'access': 'w'
                },
                'DCCVAU': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 11,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCCIMVAC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 14,
                    'Op2': 1,
                    'access': 'w'
                },
                'DCCISW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 7,
                    'CRm': 14,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIALLIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVAIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASIDIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAAIS': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 3,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLBIALL5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVA5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASID5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAA5': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 5,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLBIALL6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVA6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASID6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAA6': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 6,
                    'Op2': 3,
                    'access': 'w'
                },
                'TLBIALL7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 0,
                    'access': 'w'
                },
                'TLBIMVA7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 1,
                    'access': 'w'
                },
                'TLBIASID7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 2,
                    'access': 'w'
                },
                'TLBIMVAA7': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 8,
                    'CRm': 7,
                    'Op2': 3,
                    'access': 'w'
                },
                'PMCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PMCNTENSET': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PMCNTENCLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 2,
                    'access': 'rw'
                },
                'PMOVSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 3,
                    'access': 'rw'
                },
                'PMSWINC': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 4,
                    'access': 'w'
                },
                'PMSELR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 12,
                    'Op2': 5,
                    'access': 'rw'
                },
                'PMCCNTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 13,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PMXEVTYPER': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 13,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PMXEVCNTR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 13,
                    'Op2': 2,
                    'access': 'rw'
                },
                'PMUSERENR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 14,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PMINTENSET': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 14,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PMINTENCLR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 9,
                    'CRm': 14,
                    'Op2': 2,
                    'access': 'rw'
                },
                'TLB Lockdown Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 10,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PRRR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 10,
                    'CRm': 2,
                    'Op2': 0,
                    'access': 'rw'
                },
                'NMRR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 10,
                    'CRm': 2,
                    'Op2': 1,
                    'access': 'rw'
                },
                'PLEIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'r'
                },
                'PLEASR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'r'
                },
                'PLEFSR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 0,
                    'Op2': 4,
                    'access': 'r'
                },
                'PLEUAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'rw'
                },
                'PLEPCR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 11,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'rw'
                },
                'VBAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'MVBAR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                'ISR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'r'
                },
                'Virtualization Interrupt Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 12,
                    'CRm': 1,
                    'Op2': 1,
                    'access': 'rw'
                },
                'FCSEIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'CONTEXTIDR': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 1,
                    'access': 'rw'
                },
                'TPIDRURW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 2,
                    'access': 'rw'
                },
                'TPIDRURO': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 3,
                    'access': 'r'
                },
                'TPIDRPRW': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 13,
                    'CRm': 0,
                    'Op2': 4,
                    'access': 'rw'
                },
                'Power Control Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 15,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'Power Control Register': {
                    'CP': 15,
                    'Op1': 0,
                    'CRn': 15,
                    'CRm': 1,
                    'Op2': 0,
                    'access': 'r'
                },
                'Configuration Base Address': {
                    'CP': 15,
                    'Op1': 4,
                    'CRn': 15,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'r'
                },
                'Select Lockdown TLB Entry for read': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 4,
                    'Op2': 2,
                    'access': 'w'
                },
                'Select Lockdown TLB Entry for write': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 4,
                    'Op2': 4,
                    'access': 'w'
                },
                'Main TLB VA register': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 5,
                    'Op2': 2,
                    'access': 'rw'
                },
                'Main TLB PA register': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 6,
                    'Op2': 2,
                    'access': 'rw'
                },
                'Main TLB Attribute register': {
                    'CP': 15,
                    'Op1': 5,
                    'CRn': 15,
                    'CRm': 7,
                    'Op2': 2,
                    'access': 'rw'
                },
                'JIDR': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 0,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'JOSCR': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 1,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'JMCR': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 2,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'Jazelle Parameters Register': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 3,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'rw'
                },
                'Jazelle Configurable Opcode Translation Table Register': {
                    'CP': 14,
                    'Op1': 7,
                    'CRn': 4,
                    'CRm': 0,
                    'Op2': 0,
                    'access': 'w'
                }
            }
        },
        'GPR': {
            'count': 2,
            'registers': {
                'r0': {},
                'r1': {},
                'r2': {},
                'r3': {},
                'r4': {},
                'r5': {},
                'r6': {},
                'r7': {},
                'r8': {},
                'r9': {},
                'r10': {},
                'r11': {},
                'r12': {}
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'pc': {},
                'cpsr': {},
                'sp': {},
                'lr': {}
            }
        }
    },
    'a9_bdi': {
        # TODO: ttb1 cannot inject into bits 2, 8, 9, 11
        'GPR': {
            'count': 2,
            'registers': {
                'r0': {},
                'r1': {},
                'r2': {},
                'r3': {},
                'r4': {},
                'r5': {},
                'r6': {},
                'r7': {},
                'r8': {},
                'r9': {},
                'r10': {},
                'r11': {},
                'r12': {},
                'r13': {},
                'r14': {}
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'pc': {},
                'cpsr': {},
                # 'spsr', 'mainid', 'cachetype', 'tcmstatus', 'tlbtype',
                # 'mputype', 'multipid', 'procfeature0', 'procfeature1',
                # 'dbgfeature0', 'auxfeature0', 'memfeature0', 'memfeature1',
                # 'memfeature2', 'memfeature3', 'instrattr0', 'instrattr1',
                # 'instrattr2', 'instrattr3', 'instrattr4', 'instrattr5',
                # 'instrattr6', 'instrattr7', 'control', 'auxcontrol',
                # 'cpaccess', 'securecfg', 'securedbg', 'nonsecure',
                'ttb0': {},
                'ttb1': {},  # 'ttbc',
                'dac': {},  # 'dfsr', 'ifsr', 'dauxfsr', 'iaucfsr',
                'dfar': {},
                'ifar': {},  # 'fcsepid',
                'context': {}
            }
        }
    },
    'p2020': {
        # TODO: add pmr, spr, L2 TLB
        # TODO: check if only certain bits are read only (some partially worked)
        # TODO: ccsrbar, tsr reset after read/write?
        'GPR': {
            'count': 2,
            'registers': {
                'egpr0': {
                    'bits': 64
                },
                'egpr1': {
                    'bits': 64
                },
                'egpr2': {
                    'bits': 64
                },
                'egpr3': {
                    'bits': 64
                },
                'egpr4': {
                    'bits': 64
                },
                'egpr5': {
                    'bits': 64
                },
                'egpr6': {
                    'bits': 64
                },
                'egpr7': {
                    'bits': 64
                },
                'egpr8': {
                    'bits': 64
                },
                'egpr9': {
                    'bits': 64
                },
                'egpr10': {
                    'bits': 64
                },
                'egpr11': {
                    'bits': 64
                },
                'egpr12': {
                    'bits': 64
                },
                'egpr13': {
                    'bits': 64
                },
                'egpr14': {
                    'bits': 64
                },
                'egpr15': {
                    'bits': 64
                },
                'egpr16': {
                    'bits': 64
                },
                'egpr17': {
                    'bits': 64
                },
                'egpr18': {
                    'bits': 64
                },
                'egpr19': {
                    'bits': 64
                },
                'egpr20': {
                    'bits': 64
                },
                'egpr21': {
                    'bits': 64
                },
                'egpr22': {
                    'bits': 64
                },
                'egpr23': {
                    'bits': 64
                },
                'egpr24': {
                    'bits': 64
                },
                'egpr25': {
                    'bits': 64
                },
                'egpr26': {
                    'bits': 64
                },
                'egpr27': {
                    'bits': 64
                },
                'egpr28': {
                    'bits': 64
                },
                'egpr29': {
                    'bits': 64
                },
                'egpr30': {
                    'bits': 64
                },
                'egpr31': {
                    'bits': 64
                }
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'bbear': {},
                'bbtar': {},
                # 'altcar', 'altcbar', 'autorstsr', 'bptr', 'br0', 'br1', 'br2',
                'br3': {},  # 'br4',
                'br5': {},  # 'br6',
                'br7': {},  # 'bucsr',
                'cap_addr': {},  # 'cap_attr',
                'cap_data_hi': {},
                'cap_data_lo': {},
                'cap_ecc': {},
                # 'cap_ext_addr', 'ccsrbar', 'clkocr', 'cs0_bnds', 'cs0_config',
                # 'cs0_config_2', 'cs1_bnds', 'cs1_config', 'cs1_config_2',
                # 'cs2_bnds', 'cs2_config', 'cs2_config_2', 'cs3_bnds',
                # 'cs3_config', 'cs3_config_2',
                'csrr0': {},
                'csrr1': {},
                'ctr': {},
                'dac1': {},
                'dac2': {},  # 'dbcr0',
                'dbcr1': {},
                'dbcr2': {},  # 'dbsr',
                'ddr_cfg': {},  # 'ddr_cfg_2', 'ddr_clk_cntl',
                'ddr_data_init': {},
                'ddr_init_addr': {},  # 'ddr_init_eaddr',
                # 'ddr_interval', 'ddr_ip_rev1', 'ddr_ip_rev2',
                'ddr_mode': {},
                'ddr_mode_2': {},
                'ddr_mode_cntl': {},
                # 'ddr_wrlvl_cntl', 'ddr_zq_cntl',
                'ddrcdr_1': {},  # 'ddrcdr_2', 'ddrclkdr', 'ddrdsr_1',
                # 'ddrdsr_2',
                'dear': {},  # 'dec',
                'decar': {},  # 'devdisr', 'ecc_err_inject', 'ecmcr',
                # 'ectrstcr', 'eeatr', 'eebacr', 'eebpcr', 'eedr', 'eeer',
                # 'eehadr', 'eeladr', 'eipbrr1', 'eipbrr2', 'err_detect',
                # 'err_disable',
                'err_inject_hi': {},
                'err_inject_lo': {},  # 'err_int_en',
                # 'err_sbe', 'esr', 'fbar', 'fbcr',
                'fcr': {},
                'fir': {},  # 'fmr', 'fpar', 'gpporcr', 'hid0',
                # 'hid1',
                'iac1': {},
                'iac2': {},  # 'ivor0', 'ivor1', 'ivor2', 'ivor3',
                # 'ivor4', 'ivor5', 'ivor6', 'ivor7', 'ivor8', 'ivor9',
                # 'ivor10', 'ivor11', 'ivor12', 'ivor13', 'ivor14', 'ivor15',
                # 'ivor32', 'ivor33', 'ivor34', 'ivor35', 'ivpr', 'l1cfg0',
                # 'l1cfg1', 'l1csr0', 'l1csr1', 'l2captdatahi', 'l2captdatalo',
                # 'l2captecc', 'l2cewar0', 'l2cewar1', 'l2cewar2', 'l2cewar3',
                # 'l2cewarea0', 'l2cewarea1', 'l2cewarea2', 'l2cewarea3',
                'l2cewcr0': {},  # 'l2cewcr1',
                'l2cewcr2': {},
                'l2cewcr3': {},
                # 'l2ctl', 'l2erraddrh', 'l2erraddrl', 'l2errattr', 'l2errctl',
                # 'l2errdet', 'l2errdis', 'l2errinjctl',
                'l2errinjhi': {},
                'l2errinjlo': {},
                # 'l2errinten', 'l2srbar0', 'l2srbar1', 'l2srbarea0',
                # 'l2srbarea1', 'laipbrr1', 'laipbrr2', 'lawar0', 'lawar1',
                # 'lawar2', 'lawar3', 'lawar4', 'lawar5', 'lawar6', 'lawar7',
                # 'lawar8', 'lawar9', 'lawar10', 'lawar11', 'lawbar0',
                # 'lawbar1', 'lawbar2', 'lawbar3', 'lawbar4', 'lawbar5',
                # 'lawbar6', 'lawbar7', 'lawbar8', 'lawbar9', 'lawbar10',
                # 'lawbar11', 'lbcr', 'lbcvselcr', 'lcrr',
                'lr': {},  # 'lsdmr', 'lsor', 'lsrt',
                'ltear': {},
                'lteatr': {},  # 'ltedr', 'lteir', 'ltesr',
                # 'lurt',
                'mamr': {},
                'mar': {},  # 'mas0', 'mas1', 'mas2',
                # 'mas3', 'mas4', 'mas6', 'mas7',
                'mbmr': {},  # 'mcmr', 'mcpsumr', 'mcsr',
                'mcsrr0': {},  # 'mcsrr1',
                'mdr': {},  # 'mm_pvr', 'mm_svr',
                # 'mmucfg', 'mmucsr0', 'mrtpr', 'or0', 'or1', 'or2', 'or3',
                # 'or4', 'or5', 'or6', 'or7', 'pid', 'pid0', 'pid1', 'pid2',
                'pir': {},  # 'porbmsr', 'pordbgmsr', 'pordevsr',
                # 'porimpscr', 'porpllsr', 'powmgtcsr', 'pvr',
                # 'rstcr', 'rstrscr',
                'sp': {},  # 'spefscr',
                'sprg0': {},
                'sprg1': {},
                'sprg2': {},
                'sprg3': {},
                'sprg4': {},
                'sprg5': {},
                'sprg6': {},
                'sprg7': {},
                # 'srdscr0', 'srdscr1', 'srdscr2',
                'srr0': {},
                'srr1': {},  # 'svr', 'tbl',
                'tbu': {},  # 'tcr', 'timing_cfg_0',
                'timing_cfg_1': {},  # 'timing_cfg_2', 'timing_cfg_3',
                # 'timing_cfg_4', 'timing_cfg_5', 'tlb0cfg',
                # 'tlb1cfg', 'tsr',
                'usprg0': {}  # 'xer'
            }
        }
    }
}

calculate_target_bits(devices)
