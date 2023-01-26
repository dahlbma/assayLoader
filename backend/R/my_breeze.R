print("HI9")
lapply(c("plotly", "scales", "parallel", "foreach", "gridExtra", "grid",
         "graphics", "gplots", "ggplot2", "raster", "xtable"), library, character.only = !0)


stderr <- compiler::cmpfun(function(x){sqrt(var(x,na.rm=T)/length(na.omit(x)))})
lowsd <- compiler::cmpfun(function(x){return(mean(x)-stderr(x))})
highsd <- compiler::cmpfun(function(x){return(mean(x)+stderr(x))})
pop.sd <- compiler::cmpfun(function(x)(sqrt(var(x)*(length(x)-1)/length(x)))); 
ssmd <- compiler::cmpfun(function(x,y)round((mean(x)-mean(y))/sqrt(var(x)+var(y))));
zfactor <- compiler::cmpfun(function(x,y)round((1-(3 * (pop.sd(x)+pop.sd(y)))/(abs(mean(x)-mean(y)))),2));
robustzfactor <- compiler::cmpfun(function(x,y)round((1-(3 * (mad(x)+mad(y)))/(abs(median(x)-median(y)))),2));
mycol=c("sample"="gray50","cells"="darkgreen","cellsTR"="green1","internal1"="darkorchid1","internal2"="darkorchid2",
        "neg1"="red1","neg"="red1","DMSO"="red1","neg2"="red4","neg3"="firebrick1","neg4"="firebrick2",
        "mneg1"="tomato1","mneg2"="tomato3","pos1"="blue1","pos"="blue1","BzCl"="blue1","bzt"="magenta4",
        "pos2"="slateblue1","mpos1"="steelblue1","mpos2"="steelblue2","blanks"="cyan")
myshape=c("sample"=1,"cells"=16,"cellsTR"=16,"internal1"=16,"internal2"=16,"neg1"=16,"neg"=16,"DMSO"=16,
          "neg2"=16,"neg3"=16,"neg4"=16,"mneg1"=16,"mneg2"=16,"pos1"=16,"pos"=16,"BzCl"=16,"bzt"=16,
          "pos2"=16,"mpos1"=16,"mpos2"=16,"blanks"=16)


#######################################################################
################# outlier removal function.

outlier_remove <- compiler::cmpfun(function(x){
  qq <- unname(quantile(x, probs=c(.25, .75), na.rm = T))
  outlier_detector <- 1.5 * IQR(x, na.rm = T)
  x[x < (qq[1] - outlier_detector) | x > (qq[2] + outlier_detector)] <- NA
  x
})  
#######################################################################


setwd('/home/mats.dahlberg/assayLoader/backend/R')
load(file='qcstat.rda')


#screen_table <- read.csv(file = 'D:\\chemreg\\assayLoader\\backend\\R\\t.csv', sep='\t')
screen_table <- read.csv(file = 't.csv', sep='\t')
data_ <- unique(screen_table[c("screen_id", "Plate")]);


print(head(data_))
print(head(screen_table))

#dimnames(rawdatamat) <- list(LETTERS[1:16], 1:24); data_tbl <- reshape2::melt(as.matrix(rawdatamat))
data_tbl <- read.csv(file = 'Holmgren_test_breeze.csv', sep='\t')

#colnames(data_tbl) <- c("Row","Column","rawIntensity")

cols_ <- list("Barcode", "read_date", "screen_id", "readout", "DWell"); 
print('hi')
rows_ <- list(barcode, read_date, file_info$screen_id,
              file_info$Readout, paste0(data_tbl$Row, data_tbl$Column))
invisible(lapply(1:length(cols_), function(i) data_tbl[, cols_[[i]]] <<- rows_[[i]]))
data_tbl <- merge(data_tbl,annoframe[annoframe$Plate==file_info$Plate,],by="DWell", all.x = T)

# positive and negative controls without outliers
pos_ctrl <- outlier_remove(data_tbl$rawIntensity[data_tbl$Content %in% "POS"])
neg_ctrl <- outlier_remove(data_tbl$rawIntensity[data_tbl$Content %in% "DMSO"])
    
#Calculate percent inhibition and activation
avg_low <- mean(pos_ctrl,na.rm=T); avg_high <- mean(neg_ctrl,na.rm=T)
data_tbl$inhibition_percent <- ((avg_high-data_tbl$rawIntensity)/(avg_high-avg_low))*100







qcstat = do.call(rbind, lapply(1:dim((data_))[1], function(i){
    plate_table=screen_table[screen_table$screen_id == data_[i,1] & screen_table$Plate == data_[i,2], ]
                                        # browser()
    plate_table=plate_table[with(plate_table, order(Column)), ]
    raw_datamat <- matrix(plate_table$rawIntensity,nrow=16,ncol=24,byrow=F)
    
    productUp = toupper(plate_table$ProductName);
    pos = na.omit(plate_table$rawIntensity[productUp %in% c("BZCL","POS") & plate_table$DCol!=24]); neg = na.omit(plate_table$rawIntensity[productUp %in% c("DMSO","NEG")]);
    cells_1=plate_table$rawIntensity[plate_table$ProductName=="cells" & plate_table$Column==1]
    cells_24=plate_table$rawIntensity[plate_table$ProductName=="cells" & plate_table$Column==24]
    
    outer_negcontrols=plate_table$rawIntensity[productUp %in% c("CELLS","DMSO","NEG","DMSO") & (plate_table$Column %in% c(1,24) | plate_table$DRow %in% LETTERS[c(1,16)])]
    inner_negcontrols=plate_table$rawIntensity[productUp %in% c("CELLS","DMSO","NEG","DMSO") & (plate_table$Column %in% c(2:23) & plate_table$DRow %in% LETTERS[2:15])]
    Out_To_In_Controls=round(median(outer_negcontrols)/median(inner_negcontrols),2)
    
    if(max(plate_table$readout) %in% c("CTX","SyTxG")){
        plate_ssmd <- ssmd(pos,neg);Signal_Vs_BG=round(mean(pos)/mean(neg),1)
    }else{
        plate_ssmd <- ssmd(neg,pos);Signal_Vs_BG=round(mean(neg)/mean(pos),1)
    }
    
    data.frame(Plate = paste0(data_[i,1],"_",data_[i,2]), Z_Prime = zfactor(neg,pos), Robust_Z_Prime = robustzfactor(neg,pos),SSMD = plate_ssmd, Signal_Vs_BG = Signal_Vs_BG, Out_To_In_Controls=Out_To_In_Controls,Mean_Neg = round(mean(neg),1), SD_Neg = round(pop.sd(neg),1), CV_Neg = round(raster::cv(neg),1), Mean_Pos = round(mean(pos),1), SD_Pos = round(pop.sd(pos),1), CV_Pos = round(raster::cv(pos),1), Mean_Cells_Col1 = round(mean(cells_1),1), SD_Cells_Col1 = round(pop.sd(cells_1),1), CV_Cells_Col1 = round(raster::cv(cells_1),1), Mean_Cells_Col24 = round(mean(cells_24),1), SD_Cells_Col24 = round(pop.sd(cells_24),1), CV_Cells_Col24 = round(raster::cv(cells_24),1))
}))


