from targets import calculate_target_bits

# TODO: add ETSEC_TBI target to P2020

p2020_ccsrbar = 0xFFE00000

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
                'r12': {},
                'r8_fiq': {},
                'r9_fiq': {},
                'r10_fiq': {},
                'r11_fiq': {},
                'r12_fiq': {}
            }
        },
        'CPU': {
            'count': 2,
            'registers': {
                'cpsr': {},
                'lr': {},
                'lr_abt': {},
                'lr_fiq': {},
                'lr_irq': {},
                'lr_mon': {},
                'lr_svc': {},
                'lr_und': {},
                'lr_usr': {},
                'pc': {},
                'sp': {},
                'sp_abt': {},
                'sp_fiq': {},
                'sp_irq': {},
                'sp_mon': {},
                'sp_svc': {},
                'sp_und': {},
                'sp_usr': {},
                'spsr_abt': {},
                'spsr_fiq': {},
                'spsr_irq': {},
                'spsr_mon': {},
                'spsr_svc': {},
                'spsr_und': {}
            }
        }
    },
    'a9_bdi': {
        # TODO: ttb1 cannot inject into bits 2, 8, 9, 11
        # TODO: seperate CP registers
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
                'auxcontrol': {},
                'auxfeature0': {},
                'cachetype': {},
                'context': {},
                'control': {},
                'cpaccess': {},
                'cpsr': {},
                'dac': {},
                'dauxfsr': {},
                'dbgfeature0': {},
                'dfar': {},
                'dfsr': {},
                'fcsepid': {},
                'iaucfsr': {},
                'ifar': {},
                'ifsr': {},
                'instrattr0': {},
                'instrattr1': {},
                'instrattr2': {},
                'instrattr3': {},
                'instrattr4': {},
                'instrattr5': {},
                'instrattr6': {},
                'instrattr7': {},
                'mainid': {},
                'memfeature0': {},
                'memfeature1': {},
                'memfeature2': {},
                'memfeature3': {},
                'mputype': {},
                'multipid': {},
                'nonsecure': {},
                'pc': {},
                'procfeature0': {},
                'procfeature1': {},
                'securecfg': {},
                'securedbg': {},
                'spsr': {},
                'tcmstatus': {},
                'tlbtype': {},
                'ttb0': {},
                'ttb1': {},
                'ttbc': {}
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
                'altcar': {},
                'altcbar': {},
                'autorstsr': {},
                'bbear': {},
                'bbtar': {},
                'bptr': {},
                'br0': {},
                'br1': {},
                'br2': {},
                'br3': {},
                'br4': {},
                'br5': {},
                'br6': {},
                'br7': {},
                'bucsr': {},
                'cap_addr': {},
                'cap_attr': {},
                'cap_data_hi': {},
                'cap_data_lo': {},
                'cap_ecc': {},
                'cap_ext_addr': {},
                'ccsrbar': {},
                'clkocr': {},
                'cs0_bnds': {},
                'cs0_config': {},
                'cs0_config_2': {},
                'cs1_bnds': {},
                'cs1_config': {},
                'cs1_config_2': {},
                'cs2_bnds': {},
                'cs2_config': {},
                'cs2_config_2': {},
                'cs3_bnds': {},
                'cs3_config': {},
                'cs3_config_2': {},
                'csrr0': {},
                'csrr1': {},
                'ctr': {},
                'dac1': {},
                'dac2': {},
                'dbcr0': {},
                'dbcr1': {},
                'dbcr2': {},
                'dbsr': {},
                'ddr_cfg': {},
                'ddr_cfg_2': {},
                'ddr_clk_cntl': {},
                'ddr_data_init': {},
                'ddr_init_addr': {},
                'ddr_init_eaddr': {},
                'ddr_interval': {},
                'ddr_ip_rev1': {},
                'ddr_ip_rev2': {},
                'ddr_mode': {},
                'ddr_mode_2': {},
                'ddr_mode_cntl': {},
                'ddr_wrlvl_cntl': {},
                'ddr_zq_cntl': {},
                'ddrcdr_1': {},
                'ddrcdr_2': {},
                'ddrclkdr': {},
                'ddrdsr_1': {},
                'ddrdsr_2': {},
                'dear': {},
                'dec': {},
                'decar': {},
                'devdisr': {},
                'ecc_err_inject': {},
                'ecmcr': {},
                'ectrstcr': {},
                'eeatr': {},
                'eebacr': {},
                'eebpcr': {},
                'eedr': {},
                'eeer': {},
                'eehadr': {},
                'eeladr': {},
                'eipbrr1': {},
                'eipbrr2': {},
                'err_detect': {},
                'err_disable': {},
                'err_inject_hi': {},
                'err_inject_lo': {},
                'err_int_en': {},
                'err_sbe': {},
                'esr': {},
                'fbar': {},
                'fbcr': {},
                'fcr': {},
                'fir': {},
                'fmr': {},
                'fpar': {},
                'gpporcr': {},
                'hid0': {},
                'hid1': {},
                'iac1': {},
                'iac2': {},
                'ivor0': {},
                'ivor1': {},
                'ivor2': {},
                'ivor3': {},
                'ivor4': {},
                'ivor5': {},
                'ivor6': {},
                'ivor7': {},
                'ivor8': {},
                'ivor9': {},
                'ivor10': {},
                'ivor11': {},
                'ivor12': {},
                'ivor13': {},
                'ivor14': {},
                'ivor15': {},
                'ivor32': {},
                'ivor33': {},
                'ivor34': {},
                'ivor35': {},
                'ivpr': {},
                'l1cfg0': {},
                'l1cfg1': {},
                'l1csr0': {},
                'l1csr1': {},
                'l2captdatahi': {},
                'l2captdatalo': {},
                'l2captecc': {},
                'l2cewar0': {},
                'l2cewar1': {},
                'l2cewar2': {},
                'l2cewar3': {},
                'l2cewarea0': {},
                'l2cewarea1': {},
                'l2cewarea2': {},
                'l2cewarea3': {},
                'l2cewcr0': {},
                'l2cewcr1': {},
                'l2cewcr2': {},
                'l2cewcr3': {},
                'l2ctl': {},
                'l2erraddrh': {},
                'l2erraddrl': {},
                'l2errattr': {},
                'l2errctl': {},
                'l2errdet': {},
                'l2errdis': {},
                'l2errinjctl': {},
                'l2errinjhi': {},
                'l2errinjlo': {},
                'l2errinten': {},
                'l2srbar0': {},
                'l2srbar1': {},
                'l2srbarea0': {},
                'l2srbarea1': {},
                'laipbrr1': {},
                'laipbrr2': {},
                'lawar0': {},
                'lawar1': {},
                'lawar2': {},
                'lawar3': {},
                'lawar4': {},
                'lawar5': {},
                'lawar6': {},
                'lawar7': {},
                'lawar8': {},
                'lawar9': {},
                'lawar10': {},
                'lawar11': {},
                'lawbar0': {},
                'lawbar1': {},
                'lawbar2': {},
                'lawbar3': {},
                'lawbar4': {},
                'lawbar5': {},
                'lawbar6': {},
                'lawbar7': {},
                'lawbar8': {},
                'lawbar9': {},
                'lawbar10': {},
                'lawbar11': {},
                'lbcr': {},
                'lbcvselcr': {},
                'lcrr': {},
                'lr': {},
                'lsdmr': {},
                'lsor': {},
                'lsrt': {},
                'ltear': {},
                'lteatr': {},
                'ltedr': {},
                'lteir': {},
                'ltesr': {},
                'lurt': {},
                'mamr': {},
                'mar': {},
                'mas0': {},
                'mas1': {},
                'mas2': {},
                'mas3': {},
                'mas4': {},
                'mas6': {},
                'mas7': {},
                'mbmr': {},
                'mcmr': {},
                'mcpsumr': {},
                'mcsr': {},
                'mcsrr0': {},
                'mcsrr1': {},
                'mdr': {},
                'mm_pvr': {},
                'mm_svr': {},
                'mmucfg': {},
                'mmucsr0': {},
                'mrtpr': {},
                'or0': {},
                'or1': {},
                'or2': {},
                'or3': {},
                'or4': {},
                'or5': {},
                'or6': {},
                'or7': {},
                'pid': {},
                'pid0': {},
                'pid1': {},
                'pid2': {},
                'pir': {},
                'porbmsr': {},
                'pordbgmsr': {},
                'pordevsr': {},
                'porimpscr': {},
                'porpllsr': {},
                'powmgtcsr': {},
                'pvr': {},
                'rstcr': {},
                'rstrscr': {},
                'sp': {},
                'spefscr': {},
                'sprg0': {},
                'sprg1': {},
                'sprg2': {},
                'sprg3': {},
                'sprg4': {},
                'sprg5': {},
                'sprg6': {},
                'sprg7': {},
                'srdscr0': {},
                'srdscr1': {},
                'srdscr2': {},
                'srr0': {},
                'srr1': {},
                'svr': {},
                'tbl': {},
                'tbu': {},
                'tcr': {},
                'timing_cfg_0': {},
                'timing_cfg_1': {},
                'timing_cfg_2': {},
                'timing_cfg_3': {},
                'timing_cfg_4': {},
                'timing_cfg_5': {},
                'tlb0cfg': {},
                'tlb1cfg': {},
                'tsr': {},
                'usprg0': {},
                'xer': {}
            }
        },
        # 'TLB': {
        #     'count': 2,
        #     'registers': {
        #         'tlb0': {
        #             'bits': 32,
        #             'count': (16),
        #             'is_tlb': True,
        #             'fields': {

        #             }
        #         },
        #         'tlb1': {
        #             'bits': 32,
        #             'count': (512),
        #             'is_tlb': True,
        #             'fields': {

        #             }
        #         }
        #     }
        # }
        'ETSEC': {
            'count': 3,
            'memory_mapped': True,
            'base': [
                p2020_ccsrbar+0x24000,
                p2020_ccsrbar+0x25000,
                p2020_ccsrbar+0x26000
            ],
            'registers': {
                'TSEC_ID': {
                    'access': 'r',
                    'offset': 0x0
                },
                'TSEC_ID2': {
                    'access': 'r',
                    'offset': 0x4
                },
                'IEVENT': {
                    'access': 'w1c',
                    'offset': 0x10
                },
                'IMASK': {
                    'access': 'rw',
                    'offset': 0x14
                },
                'EDIS': {
                    'access': 'rw',
                    'offset': 0x18
                },
                'ECNTRL': {
                    'access': 'rw',
                    'offset': 0x20
                },
                'PTV': {
                    'access': 'rw',
                    'offset': 0x28
                },
                'DMACTRL': {
                    'access': 'rw',
                    'offset': 0x2C
                },
                'TBIPA': {
                    'access': 'rw',
                    'offset': 0x30
                },
                'TCTRL': {
                    'access': 'rw',
                    'offset': 0x100
                },
                'TSTAT': {
                    'access': 'w1c',
                    'offset': 0x104
                },
                'DFVLAN': {
                    'access': 'rw',
                    'offset': 0x108
                },
                'TXIC': {
                    'access': 'rw',
                    'offset': 0x110
                },
                'TQUEUE': {
                    'access': 'rw',
                    'offset': 0x114
                },
                'TR03WT': {
                    'access': 'rw',
                    'offset': 0x140
                },
                'TR47WT': {
                    'access': 'rw',
                    'offset': 0x144
                },
                'TBDBPH': {
                    'access': 'rw',
                    'offset': 0x180
                },
                'TBPTR0': {
                    'access': 'rw',
                    'offset': 0x184
                },
                'TBPTR1': {
                    'access': 'rw',
                    'offset': 0x18C
                },
                'TBPTR2': {
                    'access': 'rw',
                    'offset': 0x194
                },
                'TBPTR3': {
                    'access': 'rw',
                    'offset': 0x19C
                },
                'TBPTR4': {
                    'access': 'rw',
                    'offset': 0x1A4
                },
                'TBPTR5': {
                    'access': 'rw',
                    'offset': 0x1AC
                },
                'TBPTR6': {
                    'access': 'rw',
                    'offset': 0x1B4
                },
                'TBPTR7': {
                    'access': 'rw',
                    'offset': 0x1BC
                },
                'TBASEH': {
                    'access': 'rw',
                    'offset': 0x200
                },
                'TBASE0': {
                    'access': 'rw',
                    'offset': 0x204
                },
                'TBASE1': {
                    'access': 'rw',
                    'offset': 0x20C
                },
                'TBASE2': {
                    'access': 'rw',
                    'offset': 0x214
                },
                'TBASE3': {
                    'access': 'rw',
                    'offset': 0x21C
                },
                'TBASE4': {
                    'access': 'rw',
                    'offset': 0x224
                },
                'TBASE5': {
                    'access': 'rw',
                    'offset': 0x22C
                },
                'TBASE6': {
                    'access': 'rw',
                    'offset': 0x234
                },
                'TBASE7': {
                    'access': 'rw',
                    'offset': 0x23C
                },
                'TMR_TXTS1_ID': {
                    'access': 'r',
                    'offset': 0x280
                },
                'TMR_TXTS2_ID': {
                    'access': 'r',
                    'offset': 0x284
                },
                'TMR_TXTS1_H': {
                    'access': 'r',
                    'offset': 0x2C0
                },
                'TMR_TXTS1_L': {
                    'access': 'r',
                    'offset': 0x2C4
                },
                'TMR_TXTS2_H': {
                    'access': 'r',
                    'offset': 0x2C8
                },
                'TMR_TXTS2_L': {
                    'access': 'r',
                    'offset': 0x2CC
                },
                'RCTRL': {
                    'access': 'rw',
                    'offset': 0x300
                },
                'RSTAT': {
                    'access': 'w1c',
                    'offset': 0x304
                },
                'RXIC': {
                    'access': 'rw',
                    'offset': 0x310
                },
                'RQUEUE': {
                    'access': 'rw',
                    'offset': 0x314
                },
                'RBIFX': {
                    'access': 'rw',
                    'offset': 0x330
                },
                'RQFAR': {
                    'access': 'rw',
                    'offset': 0x334
                },
                'RQFCR': {
                    'access': 'rw',
                    'offset': 0x338
                },
                'RQFPR': {
                    'access': 'rw',
                    'offset': 0x33C
                },
                'MRBLR': {
                    'access': 'rw',
                    'offset': 0x340
                },
                'RBDBPH': {
                    'access': 'rw',
                    'offset': 0x380
                },
                'RBPTR0': {
                    'access': 'rw',
                    'offset': 0x384
                },
                'RBPTR1': {
                    'access': 'rw',
                    'offset': 0x38C
                },
                'RBPTR2': {
                    'access': 'rw',
                    'offset': 0x394
                },
                'RBPTR3': {
                    'access': 'rw',
                    'offset': 0x39C
                },
                'RBPTR4': {
                    'access': 'rw',
                    'offset': 0x3A4
                },
                'RBPTR5': {
                    'access': 'rw',
                    'offset': 0x3AC
                },
                'RBPTR6': {
                    'access': 'rw',
                    'offset': 0x3B4
                },
                'RBPTR7': {
                    'access': 'rw',
                    'offset': 0x3BC
                },
                'RBASEH': {
                    'access': 'rw',
                    'offset': 0x400
                },
                'RBASE0': {
                    'access': 'rw',
                    'offset': 0x404
                },
                'RBASE1': {
                    'access': 'rw',
                    'offset': 0x40C
                },
                'RBASE2': {
                    'access': 'rw',
                    'offset': 0x414
                },
                'RBASE3': {
                    'access': 'rw',
                    'offset': 0x41C
                },
                'RBASE4': {
                    'access': 'rw',
                    'offset': 0x424
                },
                'RBASE5': {
                    'access': 'rw',
                    'offset': 0x42C
                },
                'RBASE6': {
                    'access': 'rw',
                    'offset': 0x434
                },
                'RBASE7': {
                    'access': 'rw',
                    'offset': 0x43C
                },
                'TMR_RXTS_H': {
                    'access': 'r',
                    'offset': 0x4C0
                },
                'TMR_RXTS_L': {
                    'access': 'r',
                    'offset': 0x4C4
                },
                'MACCFG1': {
                    'access': 'rw',
                    'offset': 0x500
                },
                'MACCFG2': {
                    'access': 'rw',
                    'offset': 0x504
                },
                'IPGIFG': {
                    'access': 'rw',
                    'offset': 0x508
                },
                'HAFDUP': {
                    'access': 'rw',
                    'offset': 0x50C
                },
                'MAXFRM': {
                    'access': 'rw',
                    'offset': 0x510
                },
                'MIIMCFG': {
                    'access': 'rw',
                    'offset': 0x520
                },
                'MIIMCOM': {
                    'access': 'rw',
                    'offset': 0x524
                },
                'MIIMADD': {
                    'access': 'rw',
                    'offset': 0x528
                },
                'MIIMCON': {
                    'access': 'w',
                    'offset': 0x52C
                },
                'MIIMSTAT': {
                    'access': 'r',
                    'offset': 0x530
                },
                'MIIMIND': {
                    'access': 'r',
                    'offset': 0x534
                },
                'IFSTAT': {
                    'access': 'r',
                    'offset': 0x53C
                },
                'MACSTNADDR1': {
                    'access': 'rw',
                    'offset': 0x540
                },
                'MACSTNADDR2': {
                    'access': 'rw',
                    'offset': 0x544
                },
                'MAC01ADDR1': {
                    'access': 'rw',
                    'offset': 0x548
                },
                'MAC01ADDR2': {
                    'access': 'rw',
                    'offset': 0x54C
                },
                'MAC02ADDR1': {
                    'access': 'rw',
                    'offset': 0x550
                },
                'MAC02ADDR2': {
                    'access': 'rw',
                    'offset': 0x554
                },
                'MAC03ADDR1': {
                    'access': 'rw',
                    'offset': 0x558
                },
                'MAC03ADDR2': {
                    'access': 'rw',
                    'offset': 0x55C
                },
                'MAC04ADDR1': {
                    'access': 'rw',
                    'offset': 0x560
                },
                'MAC04ADDR2': {
                    'access': 'rw',
                    'offset': 0x564
                },
                'MAC05ADDR1': {
                    'access': 'rw',
                    'offset': 0x568
                },
                'MAC05ADDR2': {
                    'access': 'rw',
                    'offset': 0x56C
                },
                'MAC06ADDR1': {
                    'access': 'rw',
                    'offset': 0x570
                },
                'MAC06ADDR2': {
                    'access': 'rw',
                    'offset': 0x574
                },
                'MAC07ADDR1': {
                    'access': 'rw',
                    'offset': 0x578
                },
                'MAC07ADDR2': {
                    'access': 'rw',
                    'offset': 0x57C
                },
                'MAC08ADDR1': {
                    'access': 'rw',
                    'offset': 0x580
                },
                'MAC08ADDR2': {
                    'access': 'rw',
                    'offset': 0x584
                },
                'MAC09ADDR1': {
                    'access': 'rw',
                    'offset': 0x588
                },
                'MAC09ADDR2': {
                    'access': 'rw',
                    'offset': 0x58C
                },
                'MAC10ADDR1': {
                    'access': 'rw',
                    'offset': 0x590
                },
                'MAC10ADDR2': {
                    'access': 'rw',
                    'offset': 0x594
                },
                'MAC11ADDR1': {
                    'access': 'rw',
                    'offset': 0x598
                },
                'MAC11ADDR2': {
                    'access': 'rw',
                    'offset': 0x59C
                },
                'MAC12ADDR1': {
                    'access': 'rw',
                    'offset': 0x5A0
                },
                'MAC12ADDR2': {
                    'access': 'rw',
                    'offset': 0x5A4
                },
                'MAC13ADDR1': {
                    'access': 'rw',
                    'offset': 0x5A8
                },
                'MAC13ADDR2': {
                    'access': 'rw',
                    'offset': 0x5AC
                },
                'MAC14ADDR1': {
                    'access': 'rw',
                    'offset': 0x5B0
                },
                'MAC14ADDR2': {
                    'access': 'rw',
                    'offset': 0x5B4
                },
                'MAC15ADDR1': {
                    'access': 'rw',
                    'offset': 0x5B8
                },
                'MAC15ADDR2': {
                    'access': 'rw',
                    'offset': 0x5BC
                },
                'TR64': {
                    'access': 'rw',
                    'offset': 0x680
                },
                'TR127': {
                    'access': 'rw',
                    'offset': 0x684
                },
                'TR255': {
                    'access': 'rw',
                    'offset': 0x688
                },
                'TR511': {
                    'access': 'rw',
                    'offset': 0x68C
                },
                'TR1K': {
                    'access': 'rw',
                    'offset': 0x690
                },
                'TRMAX': {
                    'access': 'rw',
                    'offset': 0x694
                },
                'TRMGV': {
                    'access': 'rw',
                    'offset': 0x698
                },
                'RBYT': {
                    'access': 'rw',
                    'offset': 0x69C
                },
                'RPKT': {
                    'access': 'rw',
                    'offset': 0x6A0
                },
                'RFCS': {
                    'access': 'rw',
                    'offset': 0x6A4
                },
                'RMCA': {
                    'access': 'rw',
                    'offset': 0x6A8
                },
                'RBCA': {
                    'access': 'rw',
                    'offset': 0x6AC
                },
                'RXCF': {
                    'access': 'rw',
                    'offset': 0x6B0
                },
                'RXPF': {
                    'access': 'rw',
                    'offset': 0x6B4
                },
                'RXUO': {
                    'access': 'rw',
                    'offset': 0x6B8
                },
                'RALN': {
                    'access': 'rw',
                    'offset': 0x6BC
                },
                'RFLR': {
                    'access': 'rw',
                    'offset': 0x6C0
                },
                'RCDE': {
                    'access': 'rw',
                    'offset': 0x6C4
                },
                'RCSE': {
                    'access': 'rw',
                    'offset': 0x6C8
                },
                'RUND': {
                    'access': 'rw',
                    'offset': 0x6CC
                },
                'ROVR': {
                    'access': 'rw',
                    'offset': 0x6D0
                },
                'RFRG': {
                    'access': 'rw',
                    'offset': 0x6D4
                },
                'RJBR': {
                    'access': 'rw',
                    'offset': 0x6D8
                },
                'RDRP': {
                    'access': 'rw',
                    'offset': 0x6DC
                },
                'TBYT': {
                    'access': 'rw',
                    'offset': 0x6E0
                },
                'TPKT': {
                    'access': 'rw',
                    'offset': 0x6E4
                },
                'TMCA': {
                    'access': 'rw',
                    'offset': 0x6E8
                },
                'TBCA': {
                    'access': 'rw',
                    'offset': 0x6EC
                },
                'TXPF': {
                    'access': 'rw',
                    'offset': 0x6F0
                },
                'TDFR': {
                    'access': 'rw',
                    'offset': 0x6F4
                },
                'TEDF': {
                    'access': 'rw',
                    'offset': 0x6F8
                },
                'TSCL': {
                    'access': 'rw',
                    'offset': 0x6FC
                },
                'TMCL': {
                    'access': 'rw',
                    'offset': 0x700
                },
                'TLCL': {
                    'access': 'rw',
                    'offset': 0x704
                },
                'TXCL': {
                    'access': 'rw',
                    'offset': 0x708
                },
                'TNCL': {
                    'access': 'rw',
                    'offset': 0x70C
                },
                'TDRP': {
                    'access': 'rw',
                    'offset': 0x714
                },
                'TJBR': {
                    'access': 'rw',
                    'offset': 0x718
                },
                'TFCS': {
                    'access': 'rw',
                    'offset': 0x71C
                },
                'TXCF': {
                    'access': 'rw',
                    'offset': 0x720
                },
                'TOVR': {
                    'access': 'rw',
                    'offset': 0x724
                },
                'TUND': {
                    'access': 'rw',
                    'offset': 0x728
                },
                'TFRG': {
                    'access': 'rw',
                    'offset': 0x72C
                },
                'CAR1': {
                    'access': 'w1c',
                    'offset': 0x730
                },
                'CAR2': {
                    'access': 'rw',
                    'offset': 0x734
                },
                'CAM1': {
                    'access': 'rw',
                    'offset': 0x738
                },
                'CAM2': {
                    'access': 'rw',
                    'offset': 0x73C
                },
                'RREJ': {
                    'access': 'rw',
                    'offset': 0x740
                },
                'IGADDR0': {
                    'access': 'rw',
                    'offset': 0x800
                },
                'IGADDR1': {
                    'access': 'rw',
                    'offset': 0x804
                },
                'IGADDR2': {
                    'access': 'rw',
                    'offset': 0x808
                },
                'IGADDR3': {
                    'access': 'rw',
                    'offset': 0x80C
                },
                'IGADDR4': {
                    'access': 'rw',
                    'offset': 0x810
                },
                'IGADDR5': {
                    'access': 'rw',
                    'offset': 0x814
                },
                'IGADDR6': {
                    'access': 'rw',
                    'offset': 0x818
                },
                'IGADDR7': {
                    'access': 'rw',
                    'offset': 0x81C
                },
                'GADDR0': {
                    'access': 'rw',
                    'offset': 0x880
                },
                'GADDR1': {
                    'access': 'rw',
                    'offset': 0x884
                },
                'GADDR2': {
                    'access': 'rw',
                    'offset': 0x888
                },
                'GADDR3': {
                    'access': 'rw',
                    'offset': 0x88C
                },
                'GADDR4': {
                    'access': 'rw',
                    'offset': 0x890
                },
                'GADDR5': {
                    'access': 'rw',
                    'offset': 0x894
                },
                'GADDR6': {
                    'access': 'rw',
                    'offset': 0x898
                },
                'GADDR7': {
                    'access': 'rw',
                    'offset': 0x89C
                },
                'ATTR': {
                    'access': 'rw',
                    'offset': 0xBF8
                },
                'ATTRELI': {
                    'access': 'rw',
                    'offset': 0xBFC
                },
                'RQPRM0': {
                    'access': 'rw',
                    'offset': 0xC00
                },
                'RQPRM1': {
                    'access': 'rw',
                    'offset': 0xC04
                },
                'RQPRM2': {
                    'access': 'rw',
                    'offset': 0xC08
                },
                'RQPRM3': {
                    'access': 'rw',
                    'offset': 0xC0C
                },
                'RQPRM4': {
                    'access': 'rw',
                    'offset': 0xC10
                },
                'RQPRM5': {
                    'access': 'rw',
                    'offset': 0xC14
                },
                'RQPRM6': {
                    'access': 'rw',
                    'offset': 0xC18
                },
                'RQPRM7': {
                    'access': 'rw',
                    'offset': 0xC1C
                },
                'RFBPTR0': {
                    'access': 'rw',
                    'offset': 0xC44
                },
                'RFBPTR1': {
                    'access': 'rw',
                    'offset': 0xC4C
                },
                'RFBPTR2': {
                    'access': 'rw',
                    'offset': 0xC54
                },
                'RFBPTR3': {
                    'access': 'rw',
                    'offset': 0xC5C
                },
                'RFBPTR4': {
                    'access': 'rw',
                    'offset': 0xC64
                },
                'RFBPTR5': {
                    'access': 'rw',
                    'offset': 0xC6C
                },
                'RFBPTR6': {
                    'access': 'rw',
                    'offset': 0xC74
                },
                'RFBPTR7': {
                    'access': 'rw',
                    'offset': 0xC7C
                }
            }
        },
        'ETSEC_1588': {
            'count': 1,
            'memory_mapped': True,
            'base': [
                p2020_ccsrbar+0x24000
            ],
            'registers': {
                'TMR_CTRL': {
                    'access': 'rw',
                    'offset': 0xE00
                },
                'TMR_TEVENT': {
                    'access': 'w1c',
                    'offset': 0xE04
                },
                'TMR_TEMASK': {
                    'access': 'rw',
                    'offset': 0xE08
                },
                'TMR_PEVENT': {
                    'access': 'rw',
                    'offset': 0xE0C
                },
                'TMR_PEMASK': {
                    'access': 'rw',
                    'offset': 0xE10
                },
                'TMR_STAT': {
                    'access': 'rw',
                    'offset': 0xE14
                },
                'TMR_CNT_H': {
                    'access': 'rw',
                    'offset': 0xE18
                },
                'TMR_CNT_L': {
                    'access': 'rw',
                    'offset': 0xE1C
                },
                'TMR_ADD': {
                    'access': 'rw',
                    'offset': 0xE20
                },
                'TMR_ACC': {
                    'access': 'rw',
                    'offset': 0xE24
                },
                'TMR_PRSC': {
                    'access': 'rw',
                    'offset': 0xE28
                },
                'TMROFF_H': {
                    'access': 'rw',
                    'offset': 0xE30
                },
                'TMROFF_L': {
                    'access': 'rw',
                    'offset': 0xE34
                },
                'TMR_ALARM1_H': {
                    'access': 'rw',
                    'offset': 0xE40
                },
                'TMR_ALARM1_L': {
                    'access': 'rw',
                    'offset': 0xE44
                },
                'TMR_ALARM2_H': {
                    'access': 'rw',
                    'offset': 0xE48
                },
                'TMR_ALARM2_L': {
                    'access': 'rw',
                    'offset': 0xE4C
                },
                'TMR_FIPER1': {
                    'access': 'rw',
                    'offset': 0xE80
                },
                'TMR_FIPER2': {
                    'access': 'rw',
                    'offset': 0xE84
                },
                'TMR_ETTS1_H': {
                    'access': 'rw',
                    'offset': 0xEA0
                },
                'TMR_ETTS1_L': {
                    'access': 'rw',
                    'offset': 0xEA4
                },
                'TMR_ETTS2_H': {
                    'access': 'rw',
                    'offset': 0xEA8
                },
                'TMR_ETTS2_L': {
                    'access': 'rw',
                    'offset': 0xEAC
                }
            }
        }
    }
}

calculate_target_bits(devices)
