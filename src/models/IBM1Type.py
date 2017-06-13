# -*- coding: utf-8 -*-

#
# IBM model 1 + Alignment Type + POS Tag implementation(old) of HMM Aligner
# Simon Fraser University
# NLP Lab
#
# This is the implementation of IBM model 1 word aligner with alignment type
# and POS tags
#
import sys
import os
import time
from collections import defaultdict
from loggers import logging
from evaluators.evaluatorWithType import evaluate
__version__ = "0.2a"


# This is a private module for transmitting test results. Please ignore.
class DummyTask():
    def __init__(self, taskName="Untitled", serial="XXXX"):
        return

    def progress(self, msg):
        return


try:
    from progress import Task
except all:
    Task = DummyTask

# Constants
tagDist = [0,
           0.401, 0.264, 0.004, 0.004,
           0.012, 0.205, 0.031, 0.008,
           0.003, 0.086, 0.002]


class AlignmentModel():
    def __init__(self):
        self.logger = logging.getLogger('Model')
        self.evaluate = evaluate

        self.lambd = 1 - 1e-20
        self.lambda1 = 0.9999999999
        self.lambda2 = 9.999900827395436E-11
        self.lambda3 = 1.000000082740371E-15

        self.t = defaultdict(float)
        self.tTag = defaultdict(float)
        self.s = defaultdict(float)
        self.sTag = defaultdict(float)

        self.f_count = defaultdict(int)
        self.e_count = defaultdict(int)
        self.fe_count = defaultdict(int)
        self.pos_f_count = defaultdict(int)
        self.pos_e_count = defaultdict(int)
        self.pos_fe_count = defaultdict(int)

        self.tagMap["SEM"] = 0
        self.tagMap["FUN"] = 1
        self.tagMap["PDE"] = 2
        self.tagMap["CDE"] = 3
        self.tagMap["MDE"] = 4
        self.tagMap["GIS"] = 5
        self.tagMap["GIF"] = 6
        self.tagMap["COI"] = 7
        self.tagMap["TIN"] = 8
        self.tagMap["NTR"] = 9
        self.tagMap["MTA"] = 10
        return

    def initialiseWithTritext(self, tritext, f_count, e_count, fe_count, s):
        total_f_e_h = defaultdict(float)
        for (f, e, alignment) in tritext:
            # Initialise f_count, fe_count, e_count
            for f_i in f:
                f_count[f_i] += 1
                for e_j in e:
                    fe_count[(f_i, e_j)] += 1
            for e_j in e:
                e_count[e_j] += 1

            # Initialise total_f_e_h count
            for item in alignment:
                left, right = item.split("-")
                fwords = ''.join(c for c in left if c.isdigit() or c == ',')
                if len(fwords) != 1:
                    continue
                # Process source word
                fWord = f[int(fwords[0]) - 1]

                # Process right(target word/tags)
                tag = right[len(right) - 4: len(right) - 1]
                tagId = tagMap[tag]
                eWords = right[:len(right) - 5]
                eWords = ''.join(c for c in eWords if c.isdigit() or c == ',')
                eWords = eWords.split(',')

                if (eWords[0] != ""):
                    for eStr in eWords:
                        eWord = e[int(eStr) - 1]
                        total_f_e_h[(fWord, eWord, tagId)] += 1

        for f, e, h in total_f_e_h:
            s[(f, e, h)] =\
                total_f_e_h[(f, e, h)] / fe_count[(f, e)]

        return

    def tProbability(self, f, e):
        v = 163303
        if (f, e) in self.t:
            return self.t[(f, e)]
        return 1.0 / v

    def sProbability(self, fWord, eWord, h, fTag, eTag):
        p1 = (1 - lambda) * tagDist[h] +\
            self.lambd * self.s[(fWord, eWord, h)]
        p2 = (1 - lambda) * tagDist[h] +\
            self.lambd * self.sTag[(fTag, eTag, h)]
        p3 = tagDist[h]

        return self.lambda1 * p1 + self.lambda2 * p2 + self.lambda3 * p3

    def sProbabilityTag(self, fTag, eTag, h):
        return self.lambd * self.sTag[(fTag, eTag, h)] +\
            (1 - self.lambd) * tagDist[h]

    def trainPOSTag(self, POSTritext, iterations=5):
        self.tTag.clear()

        initialValue = 1.0 / len(self.pos_f_count)
        for key in self.pos_fe_count:
            self.tTag[key] = initialValue

        for iteration in range(iterations):
            c = defaultdict(float)
            total = defaultdict(float)
            c_feh = defaultdict(float)

            self.logger.info("Starting Iteration " + str(iteration))
            counter = 0

            for (f, e, alignment) in POSTritext:
                counter += 1
                self.task.progress("IBM1TypeS1 iter %d, %d of %d" %
                                   (iteration, counter, len(bitext),))
                for fTag in f:
                    z = 0
                    for eTag in e:
                        z += self.tTag[(fTag, eTag)]
                    for eWord in e:
                        c[(fTag, eTag)] += self.tTag[(fTag, eTag)] / z
                        total[eTag] += self.tTag[(fTag, eTag)] / z
                        for h in range(len(self.tagMap)):
                            c_feh[(fTag, eTag, h)] +=\
                                self.tTag[fTag, eTag] *\
                                self.sProbabilityTag(fTag, eTag, h) /\
                                z

            for (fTag, eTag) in self.fe_count:
                self.tTag[(fTag, eTag)] = c[(fTag, eTag)] / total[eTag]

            for f, e, h in c_feh:
                self.sTag[(fTag, eTaf, h)] =\
                    c_feh[(fTag, eTag, h)] / c[(fTag, eTag)]
        return

    def trainFORM(self, FORMTritext, POSTritext, iterations=5):
        self.t.clear()

        initialValue = 1.0 / len(self.f_count)
        for key in self.fe_count:
            self.t[key] = initialValue

        for iteration in range(iterations):
            c = defaultdict(float)
            total = defaultdict(float)
            c_feh = defaultdict(float)

            self.logger.info("Starting Iteration " + str(iteration))
            counter = 0

            for (f, e, ) in tritext:
                fTags, eTags, = POStritext[counter]

                counter += 1
                self.task.progress("IBM1TypeS2 iter %d, %d of %d" %
                                   (iteration, counter, len(bitext),))

                for fWord, fTag in zip(f, fTags):
                    z = 0
                    for eWord, eTag in zip(e, eTags):
                        z += self.t[(fWord, eWord)]

                    for eWord, eTag in zip(e, eTags):
                        c[(fWord, eWord)] += self.t[(fWord, eWord)] / z
                        total[eWord] += self.t[(fWord, eWord)] / z
                        for h in range(len(self.tagMap)):
                            c_feh[(fWord, eWord, h)] +=\
                                self.t[fWord, eWord] / z *\
                                self.sProbability(fWord, eWord, h, fTag, eTag)

            for (f, e) in self.fe_count:
                self.t[(f, e)] = c[(f, e)] / total[e]
            for f, e, h in c_feh:
                self.s[(f, e, h)] = c_feh[(f, e, h)] / c[(f, e)]
        return

    def train(self, tritext, POSTritext, iterations=5):
        self.task = Task("Aligner", "IBM1TypeI" + str(iterations))
        self.logger.info("Model IBM1Type, Starting Training Process")
        self.logger.info("Training size: " + str(len(tritext)))

        self.logger.info("Stage 1 Start Training with POS Tags")
        self.pos_f_count.clear()
        self.pos_e_count.clear()
        self.pos_fe_count.clear()
        self.sTag.clear()

        self.initialiseWithTritext(tritext=POSTritext,
                                   f_count=self.pos_f_count,
                                   e_count=self.pos_e_count,
                                   fe_count=self.pos_fe_count,
                                   s=self.sTag)

        self.logger.info("Stage 1 Initialisation complete")
        startTime = time.time()

        self.trainPOSTag(POSTritext, iterations)

        endTime = time.time()
        self.logger.info("Stage 1 Training Complete, total time(seconds): %f" %
                         (endTime - startTime,))

        self.logger.info("Stage 2 Start Training with words")
        self.f_count.clear()
        self.e_count.clear()
        self.fe_count.clear()
        self.s.clear()
        self.initialiseWithTritext(tritext=tritext,
                                   f_count=self.f_count,
                                   e_count=self.e_count,
                                   fe_count=self.fe_count,
                                   s=self.s)

        startTime = time.time()
        self.trainFORM(tritext, POSTritext, iterations=5)
        endTime = time.time()
        self.logger.info("Stage 2 Training Complete, total time(seconds): %f" %
                         (endTime - startTime,))
        return

    def decode(self, bitext, POSBitext, useAlignmentType):
        linkMap = ["SEM", "FUN", "PDE", "CDE",
                   "MDE", "GIS", "GIF", "COI",
                   "TIN", "NTR", "MTA"]
        self.logger.info("Start decoding")
        self.logger.info("Testing size: " + str(len(bitext)))
        result = []

        for (f, e), (fTags, eTags) in zip(bitext, POSBitext):
            sentenceAlignment = []

            for i in range(len(f)):
                max_ts = 0
                argmax = -1
                bestTagID = -1
                for j in range(len(e)):
                    t = self.tProbability(f[i], e[j])

                    for h in range(len(self.tagMap)):
                        s = self.sProbability(f[i], e[j], h,
                                              fTags(i), eTags(j))
                        if t * s > max_ts:
                            max_ts = t_SiDj * s_SiDj
                            argmax = j
                            bestTagID = h

                sentenceAlignment.append(
                    (i + 1, argmax + 1, linkMap[bestTagID]))

            result.append(sentenceAlignment)
        self.logger.info("Decoding Complete")
        return result
