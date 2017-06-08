def evaluate(bitext, result, reference):
    totalAlign = 0
    totalCertain = 0

    totalCertainAlignment = 0
    totalProbableAlignment = 0

    for i in range(min(len(result), len(reference))):
        testAlign = result[i]
        goldAlign = reference[i]

        size_f = len(bitext[i][0].strip.split())
        size_e = len(bitext[i][1].strip.split())

        for entry in testAlign:
            f = int(entry[0])
            e = int(entry[1])
            if (f > size_f or e > size_e):
                logger.error("NOT A VALID LINK")
                logger.info(i + " " +
                            f + " " + size_f + " " +
                            e + " " + size_e)

        # grade
        certainAlign = goldAlign["certain"]
        probableAlign = goldAlign["probable"]

        totalAlign += len(testAlign)
        totalCertain += len(certainAlign)

        totalCertainAlignment += len(
            [item for item in testAlign if item in certainAlign])
        totalProbableAlignment += len(
            [item for item in testAlign if item in certainAlign])
        totalProbableAlignment += len(
            [item for item in testAlign if item in probableAlign])

    precision = float(totalProbableAlignment) / totalAlign
    recall = float(totalCertainAlignment) / totalCertain
    aer = 1 -\
        ((float(totalCertainAlignment + totalProbableAlignment) /
         (totalAlign + totalCertain)))
    fScore = 2 * precision * recall / (precision + recall)

    logger.info("Precision = " + str(precision))
    logger.info("Recall    = " + str(recall))
    logger.info("AER       = " + str(aer))
    logger.info("F-score   = " + str(fScore))
    return
