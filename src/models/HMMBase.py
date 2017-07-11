# -*- coding: utf-8 -*-

#
# HMM model base of HMM Aligner
# Simon Fraser University
# NLP Lab
#
# This is the base model for HMM
#
import sys
import time
import numpy as np
from math import log
from collections import defaultdict
from copy import deepcopy

from loggers import logging
from models.modelBase import Task
from models.modelBase import AlignmentModelBase as Base
from evaluators.evaluator import evaluate
__version__ = "0.4a"


class AlignmentModelBase(Base):
    def __init__(self):
        if "nullEmissionProb" not in vars(self):
            self.nullEmissionProb = 0.000005
        if "task" not in vars(self):
            self.task = None

        if "t" not in vars(self):
            self.t = []
        if "eLengthSet" not in vars(self):
            self.eLengthSet = defaultdict(int)
        if "a" not in vars(self):
            self.a = [[[]]]
        if "pi" not in vars(self):
            self.pi = []

        if "logger" not in vars(self):
            self.logger = logging.getLogger('HMMBASE')
        if "modelComponents" not in vars(self):
            self.modelComponents = ["t", "pi", "a", "eLengthSet",
                                    "fLex", "eLex", "fIndex", "eIndex"]
        Base.__init__(self)
        return

    def initialValues(self, Len):
        self.a[:Len + 1, :Len, :Len].fill(1.0 / Len)
        self.pi[:Len].fill(1.0 / 2 / Len)
        return

    def initialiseParameter(self, maxE):
        self.a = np.zeros((maxE + 1, maxE * 2, maxE * 2))
        self.pi = np.zeros(maxE * 2)
        return

    def forwardBackward(self, f, e, tSmall, a):
        alpha = np.zeros((len(f), len(e)))
        beta = np.zeros((len(f), len(e)))
        alphaScale = np.zeros(len(f))

        alpha[0] = tSmall[0] * self.pi[:len(e)]
        alphaScale[0] = 1 / np.sum(alpha[0])
        alpha[0] *= alphaScale[0]
        for i in range(1, len(f)):
            alpha[i] = tSmall[i] * np.matmul(alpha[i - 1], a)
            alphaScale[i] = 1 / np.sum(alpha[i])
            alpha[i] *= alphaScale[i]

        beta[len(f) - 1].fill(alphaScale[len(f) - 1])
        for i in range(len(f) - 2, -1, -1):
            beta[i] =\
                np.matmul(beta[i + 1] * tSmall[i + 1], a.T) * alphaScale[i]
        return alpha, alphaScale, beta

    def maxTargetSentenceLength(self, dataset):
        maxLength = 0
        eLengthSet = defaultdict(int)
        for (f, e, alignment) in dataset:
            tempLength = len(e)
            if tempLength > maxLength:
                maxLength = tempLength
            eLengthSet[tempLength] += 1
        return (maxLength, eLengthSet)

    def baumWelch(self, dataset, iterations=5, index=0):
        if not self.task:
            self.task = Task("Aligner", "HMMBaumWelchOI" + str(iterations))
        self.logger.info("Starting Training Process")
        self.logger.info("Training size: " + str(len(dataset)))
        startTime = time.time()

        maxE, self.eLengthSet = self.maxTargetSentenceLength(dataset)
        self.logger.info("Maximum Target sentence length: " + str(maxE))
        self.initialiseParameter(maxE)

        for iteration in range(iterations):
            self.logger.info("BaumWelch Iteration " + str(iteration))
            logLikelihood = 0
            self.delta = np.zeros((maxE + 1, maxE, maxE))
            self._beginningOfIteration(dataset, maxE, index)

            counter = 0
            for (f, e, alignment) in dataset:
                self.task.progress("BaumWelch iter %d, %d of %d" %
                                   (iteration, counter, len(dataset),))
                counter += 1
                if iteration == 0:
                    self.initialValues(len(e))

                fLen, eLen = len(f), len(e)
                a = self.aProbability(f, e)[:len(e), :len(e)]
                tSmall = self.tProbability(f, e, index)

                alpha, alphaScale, beta = self.forwardBackward(f, e, tSmall, a)

                # Update logLikelihood
                logLikelihood -= np.sum(np.log(alphaScale))

                # Setting gamma
                gamma = self.gamma(f, e, alpha, beta, alphaScale, index)

                # Update delta
                Xceta = np.matmul(alpha[:fLen - 1].T, (beta * tSmall)[1:]) * a
                c = np.zeros(eLen * 2)
                for j in range(eLen):
                    c[eLen - 1 - j:2 * eLen - 1 - j] += Xceta[j]
                for j in range(eLen):
                    self.delta[eLen][j][:eLen] +=\
                        c[eLen - 1 - j:2 * eLen - 1 - j]
            # end of loop over dataset

            self.logger.info("likelihood " + str(logLikelihood))
            # M-Step
            self._updateEndOfIteration(maxE, index)

        self.endOfBaumWelch(index)
        endTime = time.time()
        self.logger.info("Training Complete, total time(seconds): %f" %
                         (endTime - startTime,))
        return

    def _beginningOfIteration(self, dataset, maxE, index):
        raise NotImplementedError

    def gamma(self, f, e, alpha, beta, alphaScale, index):
        raise NotImplementedError

    def _updateDelta(self, f, e, alpha, beta, alphaScale, tSmall, a):
        fLen, eLen = len(f), len(e)
        Xceta = np.matmul(alpha[:fLen - 1].T, (beta * tSmall)[1:]) * a
        c = np.zeros(eLen * 2)
        for j in range(eLen):
            c[eLen - 1 - j:2 * eLen - 1 - j] += Xceta[j]
        for j in range(eLen):
            self.delta[eLen][j][:eLen] +=\
                c[eLen - 1 - j:2 * eLen - 1 - j]

    def _updateEndOfIteration(self, maxE, index):
        raise NotImplementedError

    def endOfBaumWelch(self, index):
        raise NotImplementedError

    def tProbability(self, f, e, index=0):
        t = np.zeros((len(f), len(e)))
        for j in range(len(e)):
            if e[j][index] == 424242424243:
                t[:, j].fill(self.nullEmissionProb)
                continue
            if e[j][index] >= len(self.eLex[index]):
                continue
            for i in range(len(f)):
                if f[i][index] < len(self.t) and \
                        e[j][index] in self.t[f[i][index]]:
                    t[i][j] = self.t[f[i][index]][e[j][index]]
        t[t == 0] = 0.000006123586217
        return t

    def aProbability(self, f, e):
        targetLength = len(e)
        if targetLength in self.eLengthSet:
            return self.a[targetLength][:targetLength * 2, :targetLength * 2]
        return np.full((targetLength * 2, targetLength * 2), 1. / targetLength)

    def logViterbi(self, f, e):
        e = deepcopy(e)
        with np.errstate(invalid='ignore', divide='ignore'):
            a = np.log(self.aProbability(f, e))
        fLen, eLen = len(f), len(e)
        for i in range(eLen):
            e.append((424242424243, 424242424243))
        score = np.zeros((fLen, eLen * 2))
        prev_j = np.zeros((fLen, eLen * 2))

        with np.errstate(invalid='ignore', divide='ignore'):
            score = np.log(self.tProbability(f, e))
        for i in range(fLen):
            if i == 0:
                with np.errstate(invalid='ignore', divide='ignore'):
                    if 2 * eLen <= self.pi.shape[0]:
                        score[i] += np.log(self.pi[:eLen * 2])
                    else:
                        score[i][:self.pi.shape[0]] += np.log(self.pi)
                        score[i][self.pi.shape[0]:].fill(-sys.maxint)
            else:
                tmp = (a.T + score[i - 1]).T
                bestPrev_j = np.argmax(tmp, axis=0)
                prev_j[i] = bestPrev_j
                score[i] += np.max(tmp, axis=0)

        maxScore = -sys.maxint - 1
        best_j = 0
        for j in range(eLen * 2):
            if score[fLen - 1][j] > maxScore:
                maxScore = score[fLen - 1][j]
                best_j = j

        trace = [(best_j + 1, )]
        i = fLen - 1
        j = best_j

        while (i > 0):
            j = int(prev_j[i][j])
            trace = [(j + 1, )] + trace
            i = i - 1
        return trace

    def decodeSentence(self, sentence):
        f, e, alignment = self.lexiSentence(sentence)
        sentenceAlignment = []
        bestAlign = self.logViterbi(f, e)

        for i in range(len(bestAlign)):

            if bestAlign[i][0] <= len(e):
                if len(bestAlign[i]) > 1 and "typeList" in vars(self):
                    sentenceAlignment.append(
                        (i + 1, bestAlign[i][0],
                         self.typeList[bestAlign[i][1]]))
                else:
                    sentenceAlignment.append((i + 1, bestAlign[i][0]))
        return sentenceAlignment
