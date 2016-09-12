# VBG: For better computational efficiency BioSeq, BioSeqAln
# can use numpy chararrays instead of the current dictionaries, or 
# an inbuilt PyCogent(GPL) sequence/aln object with modifications

from collections import OrderedDict
import copy
import re

from napa.utils.general import *
from napa.seq.parse import *
from napa.seq.format import *

class BioSeq(object):

    def __init__(self, seq_id = 'seqid', 
                 seq_str = '', 
                 seq_type = '', 
                 seq_pos_list = [],
                 seq_annot = {'':['']}):

        self.seq_id = seq_id
        self.seq_str = seq_str
        self.length = len(self.seq_str)

        if len(seq_type): 
            self.seq_type = seq_type 
        else:
            self.determine_seq_type(seq_str)

        self.assign_standard_chars()
        self.get_seq_pos(seq_pos_list)
        self.seq_annot = seq_annot


    def __repr__(self):
        return '\t'.join([str(el) for el in \
                          [self.seq_id, self.seq_str, self.seq_type, 
                           str(self.seq_annot)]])


    def add_annot(self, annot_dict):
        self.seq_annot.update(annot_dict)


    def get_seq_pos(self, seq_pos_list):
        if not len(seq_pos_list):
            stderr_write(['BioSeq WARNING: Initialized alignment positions\n',
                          '\tto default range 1..', len(self.seq_str), 
                          'for sequence with id:', self.seq_id])
            self.seq_pos_list = range(1, len(self.seq_str)+1)
        else:
            assert (len(seq_pos_list) == self.length), \
                'Lengths of sequence string and sequence position list ' + \
                'do not match: ' + ' '.join([str(el) \
                                             for el in [self.seq_id, self.length, 
                                                        len(seq_pos_list)]])
            self.seq_pos_list = seq_pos_list


    def extract_pos(self, pos_subset):
        seq_str = ''
        for posi, pos in enumerate(self.seq_pos_list):
            if pos in pos_subset:
                seq_str += self.seq_str[posi]
        self.seq_str = seq_str
        self.seq_pos_list = copy.deepcopy(pos_subset)
        self.length = len(self.seq_str)


    def determine_seq_type(self, seq_str):
        seq_char_set =  set(list(seq_str))
        if seq_char_set <= set(list('ATGC')):
            self.seq_type = 'DNA'
        elif seq_char_set <= set(list('AUGC')):
            self.seq_type = 'RNA'
        elif seq_char_set <= set(list('ACDEFGHIKLMNPQRSTVWY')):
            self.seq_type = 'Protein'
        else:
            self.seq_type = 'unknown'
        assert (self.seq_type in ['DNA','RNA','Protein']), \
            'Could not determine sequence type.' + \
            'Please enter standard Protein/DNA/RNA seq.'


    def assign_standard_chars(self):
        seq_type_to_chars = {'DNA':'ATGC', 'RNA':'AUGC', 
                             'Protein':'ACDEFGHIKLMNPQRSTVWY'}
        self.standard_chars = seq_type_to_chars[self.seq_type]


    def get_substitutions(self, other):
        '''
        Finds substitutions only (not insertions or deletions)
        between two sequences in alignment, considering 
        standard and unambiguous sequence characters only.
        (Needs proper error handling).
        '''

        if self.length != other.length or \
           self.seq_pos_list != other.seq_pos_list:
            stderr_write(['Need to align sequences before comparing'])
            return

        if self.seq_type != other.seq_type:
            stderr_write(['Sequences have distinct sequence types!'])
            stderr_write(['Can\'t compare sequences with IDS:', 
                          self.seq_id, 'and', other.seq_id])
            return 

        mut_list = []
        for i in range(self.length):
            if self.seq_str[i] != other.seq_str[i]:
                if self.seq_str[i] in self.standard_chars and \
                   other.seq_str[i] in self.standard_chars:
                    pos = str(self.seq_pos_list[i])
                    mut_list.append(self.seq_str[i] + pos + \
                                    other.seq_str[i])

        return mut_list



class BioSeqAln(object):
    
    def __init__(self, **kwargs):
        self.seq_type = kwargs.get('seq_type', 'Protein')
        self.seq_annot = kwargs.get('seq_annot', {'':''}) 
        self.aln_pos = kwargs.get('aln_pos', [])

        if len(kwargs.get('seqid_to_seq', {})):
            self.seqid_to_seq = copy.deepcopy(kwargs.get('seqid_to_seq', {}))
        elif len(kwargs.get('aln_fasta_file', '')):
            self.seqs_from_fasta_file(kwargs.get('aln_fasta_file', ''))

        if len(kwargs.get('annot_key', '')) and \
           (len(kwargs.get('seqid_to_annot_file', '')) or \
            len(kwargs.get('seqid_to_annot', {}))):
            self.annot_seqs(kwargs.get('annot_key', ''),
                            kwargs.get('seqid_to_annot_file', ''),
                            kwargs.get('seqid_to_annot', {}))
        
        if len(kwargs.get('sel_annot_key', '')) and \
            (kwargs.get('sel_annot_list', ['']) != [''] or \
            len(kwargs.get('sel_annot_file', ''))):
            self.subset_annot_seq_dict(sel_annot_key = kwargs.get('sel_annot_key', ''),
                                       sel_annot_file = kwargs.get('sel_annot_file', ''),
                                       sel_annot_list = kwargs.get('sel_annot_list', ['']))

        if len(kwargs.get('pos_subset', [])):
            self.subset_aln_pos(kwargs.get('pos_subset', []))

        if not len(self.aln_pos):
            stderr_write(['WARNING (BioSeqAln):',
                         'Default alignment positions set.'])
            self.aln_pos = self.seqid_to_seq[self.seqid_to_seq.keys()[0]].seq_pos_list

        self.depth = len(self.seqid_to_seq)
        self.length = len(self.aln_pos)



    def seqs_from_fasta_file(self, aln_fasta_file):
        self.seqid_to_seq = OrderedDict()
        self.add_sequences_from_file(aln_fasta_file)


    def add_sequences_from_file(self, aln_fasta_file):
        fasta_recs = fasta_iter(aln_fasta_file)
    
        for r in fasta_recs:
            seq_id, seq_str = r[0], r[1]
            seq_id = re.sub('[!@#$.]|','',seq_id)
            self.seqid_to_seq[seq_id] = BioSeq(seq_id = seq_id,
                                               seq_str = seq_str,
                                               seq_type = self.seq_type,
                                               seq_pos_list = self.aln_pos,
                                               seq_annot = \
                                               copy.deepcopy(self.seq_annot))


    def annot_seqs(self, annot_key = '', seqid_to_annot_file = '',
                   seqid_to_annot = {}):
        '''
        Add sequence annotation to sequences in alignment.
        '''
        if len(seqid_to_annot_file):
            aln_seqid_to_annot = parse_keyval_dict(seqid_to_annot_file)
        elif len(seqid_to_annot):
            aln_seqid_to_annot = seqid_to_annot
        else:
            stderr_write('WARNING (BioSeqAln): No functions assigned')
        for seqid in aln_seqid_to_annot:
            seqid_fasta = re.sub('[!@#$.]|','', seqid)
            if seqid_fasta in self.seqid_to_seq:
                self.seqid_to_seq[seqid_fasta].add_annot(\
                                {annot_key: aln_seqid_to_annot[seqid]})


    def subset_aln_pos(self, pos_subset = []):
        if not len(pos_subset):
            return # No subsetting of columns
        for seqid in self.seqid_to_seq:
            self.seqid_to_seq[seqid].extract_pos(pos_subset)
        self.aln_pos = pos_subset
        self.length = len(pos_subset)


    def seqids_with_annot(self, annot_key, annot_list):
        seqid_annot = []
        for seqid in self.seqid_to_seq:
            if annot_key not in self.seqid_to_seq[seqid].seq_annot:
                continue
            if self.seqid_to_seq[seqid].seq_annot[annot_key] in annot_list:
                seqid_annot.append(seqid)
        return seqid_annot

                                                         
    def subset_annot_seq_dict(self,sel_annot_key = '', sel_annot_file = '', 
                              sel_annot_list = ['']):
                                        
        '''
        Subset alignment sequences by a sequence id 
        using a sequence dictionary based on sequence annotation
        e.g. only sequences having a given function.
        '''
        if sel_annot_list != [''] and len(sel_annot_file):
            sel_annot_list = parse_column(sel_annot_file)

        seqid_to_seq_annot = OrderedDict()
        for seqid in self.seqids_with_annot(sel_annot_key, sel_annot_list):
            seqid_to_seq_annot[seqid] = copy.deepcopy(self.seqid_to_seq[seqid])
        
        self.seqid_to_seq.clear()
        self.seqid_to_seq = copy.deepcopy(seqid_to_seq_annot)


    def get_seq_muts(self, wt_seq = ''):
        '''
        Obtain mutations between each alignment sequence and
        a reference sequence.
        '''
        self.seqid_to_mut = OrderedDict()
        for seqid in self.seqid_to_seq:
            self.seqid_to_mut[seqid] = wt_seq.get_substitutions(\
                                                    self.seqid_to_seq[seqid])

    def get_seq_muts_id(self, wt_id = ''):
        
        try:
            assert wt_id in self.seqid_to_seq
            wt_seq = self.seqid_to_seq[wt_id]
            self.get_seq_muts(wt_seq)
        
        except AssertionError:
            stderr_write(['BioSeqAln ERROR: Sequence id not in',
                          'alignment. Cannot extract mutations!'])


    def get_seq_muts_id_seq(self, wt_id = '', wt_seq_str = ''):
        
        if len(wt_id) and len(wt_seq_str):
            if wt_id in self.seqid_to_seq:
                if self.seqid_to_seq[wt_id].seq_str == wt_seq_str:
                    self.get_muts_id(wt_id)
                else:
                    stderr_write(['BioSeqAln WARNING:',
                                  'WT present in alignment but',
                                  'with different id.'])
                    wt_seq = BioSeq(wt_id, wt_seq_str, self.aln_pos)
                    self.get_seq_muts(wt_seq)
            else:
                wt_seq = BioSeq(wt_id, wt_seq_str, self.aln_pos)
                self.get_seq_muts(wt_seq)

        elif not len(wt_id) and len(wt_seq_str):
            wt_id = 'WildType'
            wt_seq = BioSeq(wt_id, wt_seq_str, self.aln_pos)
            self.get_seq_muts(wt_seq)

        elif len(wt_id) and not len(wt_seq_str):
            self.get_seq_muts_id(wt_id)

    def __repr__(self):
        out_str = ''
        for seqid in self.seqid_to_seq:
            out_str += write_wrap_fasta_seq(seqid+ '___' + '__'.join(\
                                                        ['_'.join(ann_pair) for ann_pair in \
                                                         self.seqid_to_seq[seqid].seq_annot.items() \
                                                         if '' not in ann_pair]), 
                                            self.seqid_to_seq[seqid].seq_str)
        return out_str

    def write_muts(self, out_file, pos_subset):
        with open(out_file, 'wb') as of:
            for seqid in self.seqid_to_mut:
                if len(pos_subset):
                    of.write('\t'.join(seqid, 
                                   ','.join([mut for mut in self.seqid_to_mut[seqid] \
                                             if mut in pos_subset]))+'\n')
                else:
                    of.write('\t'.join(seqid, ','.join(self.seqid_to_mut[seqid]))+'\n')


