from electroncash.i18n import _, language
from . import utils
from . import gui
from .custom_objc import TxDetailBase, TxInputsOutputsTVCBase
from .uikit_bindings import *
from .history import HistoryEntry, StatusImages
from . import addresses
from electroncash.transaction import Transaction
from electroncash.address import Address, PublicKey
from electroncash.util import timestamp_to_datetime
import json, sys
from . import coins

# ViewController used for the TxDetail view's "Inputs" and "Outputs" tables.. not exposed.. managed internally
class TxInputsOutputsTVC(TxInputsOutputsTVCBase):
    
    tagin = objc_property()
    tagout = objc_property()
    ts = objc_property()
    # weak properties from Base:
    #  txDetailVC; // the TxDetail that is holding us
    @objc_method
    def initWithInputTV_outputTV_timestamp_(self, inputTV : ObjCInstance, outputTV : ObjCInstance, ts : float) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if self is not None:
            if not isinstance(utils.nspy_get(self), Transaction):
                raise ValueError('TxInputsOutputsTVC requires an nspy entry on self that is a Transaction subclass!')
            if inputTV.tag == 0:
                inputTV.tag = 9001
            self.tagin = inputTV.tag
            if outputTV.tag == 0:
                outputTV.tag = self.tagin + 1
            self.tagout = outputTV.tag
            self.ts = ts
            
            if self.tagin == self.tagout or inputTV.ptr.value == outputTV.ptr.value:
                raise ValueError("The input and output table views must be different and have different tags!")
            
            inputTV.delegate = self
            outputTV.delegate = self
            inputTV.dataSource = self
            outputTV.dataSource = self
            
            from rubicon.objc.runtime import libobjc            
            libobjc.objc_setAssociatedObject(inputTV.ptr, self.ptr, self.ptr, 0x301)
            libobjc.objc_setAssociatedObject(outputTV.ptr, self.ptr, self.ptr, 0x301)
        return self
    
    @objc_method
    def dealloc(self) -> None:
        print("TxInputsOutputsTVC dealloc")
        self.tagin = None
        self.tagout = None
        self.ts = None
        utils.nspy_pop(self)
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def numberOfSectionsInTableView_(self, tv) -> int:
        return 1
    
    @objc_method
    def tableView_titleForHeaderInSection_(self, tv : ObjCInstance,section : int) -> ObjCInstance:
        tx = utils.nspy_get(self)
        if tv.tag == self.tagin: return _("Inputs") + " (%d) "%len(tx.inputs())
        elif tv.tag == self.tagout: return _("Outputs") + " (%d) "%len(tx.outputs())
        return "*ERROR*"
            
    @objc_method
    def tableView_numberOfRowsInSection_(self, tv : ObjCInstance, section : int) -> int:
        tx = utils.nspy_get(self)
        
        if tv.tag == self.tagin:
            return len(tx.inputs())
        elif tv.tag == self.tagout:
            return len(tx.outputs())

    @objc_method
    def tableView_cellForRowAtIndexPath_(self, tv, indexPath):
        #todo: - allow for label editing (popup menu?)
        identifier = "%s_%s"%(str(__class__) , str(indexPath.section))
        cell = tv.dequeueReusableCellWithIdentifier_(identifier)
        parent = gui.ElectrumGui.gui
        wallet = parent.wallet
        
        def format_amount(amt):
            return parent.format_amount(amt, whitespaces = True)
        
        def fx():
            return parent.daemon.fx if parent.daemon and parent.daemon.fx and parent.daemon.fx.show_history() else None

        if cell is None:
            cell = UITableViewCell.alloc().initWithStyle_reuseIdentifier_(UITableViewCellStyleSubtitle, identifier).autorelease()
        try:
            tx = utils.nspy_get(self)
        
            isInput = None
            x = None
            if tv.tag == self.tagin:
                isInput = True
                x = tx.inputs()[indexPath.row]
            elif tv.tag == self.tagout:
                isInput = False
                x = tx.get_outputs()[indexPath.row]
            else:
                raise ValueError("tv tag %d is neither input (%d) or output (%d) tag!"%(int(tv.tag),int(self.tagin),int(self.tagout)))
            
            colorExt = UIColor.colorWithRed_green_blue_alpha_(1.0,1.0,1.0,0.0)
            colorChg = utils.uicolor_custom('change address')  # UIColor.colorWithRed_green_blue_alpha_(1.0,0.9,0.3,0.3)
            colorMine = UIColor.colorWithRed_green_blue_alpha_(0.0,1.0,0.0,0.1)

            cell.backgroundColor = colorExt
            addr = None
            
            if isInput:
                if x['type'] == 'coinbase':
                    cell.textLabel.text = "coinbase"
                    cell.detailTextLabel.text = ""
                else:
                    prevout_hash = x.get('prevout_hash')
                    prevout_n = x.get('prevout_n')
                    mytxt = ""
                    mytxt += prevout_hash[0:8] + '...'
                    mytxt += prevout_hash[-8:] + (":%-4d " % prevout_n)
                    addr = x['address']
                    if isinstance(addr, PublicKey):
                        addr = addr.toAddress()
                    if addr is None:
                        addr_text = _('unknown')
                    else:
                        addr_text = addr.to_ui_string()
                    cell.textLabel.text = addr_text
                    if x.get('value') is not None:
                        v_in = x['value']
                        mytxt += format_amount(v_in)
                        if fx(): mytxt += ' (' + fx().historical_value_str(v_in,timestamp_to_datetime(self.ts)) + " " + fx().get_currency() + ')'
                    cell.detailTextLabel.text = mytxt
            else:
                colorMine = UIColor.colorWithRed_green_blue_alpha_(1.0,0.0,1.0,0.1)
                addr, v = x
                #cursor.insertText(addr.to_ui_string(), text_format(addr))
                cell.textLabel.text = addr.to_ui_string()
                cell.detailTextLabel.text = ""
                if v is not None:
                    cell.detailTextLabel.text = format_amount(v) + ((' (' + fx().historical_value_str(v,timestamp_to_datetime(self.ts)) + " " + fx().get_currency() + ')') if fx() else '')

            cell.textLabel.adjustsFontSizeToFitWidth = True
            cell.textLabel.minimumScaleFactor = 0.85

            if isinstance(addr, Address) and wallet.is_mine(addr):
                if wallet.is_change(addr):
                    cell.backgroundColor = colorChg
                else:
                    cell.backgroundColor = colorMine
                
            cell.accessoryType = UITableViewCellAccessoryNone #UITableViewCellAccessoryDisclosureIndicator#UITableViewCellAccessoryDetailDisclosureButton#UITableViewCellAccessoryDetailButton #
        except Exception as e:
            print("exception in %s: %s"%(__class__.name,str(e)))
            cell.textLabel.attributedText = None
            cell.textLabel.text = "*Error*"
            cell.detailTextLabel.attributedText = None
            cell.detailTextLabel.text = None
            cell.accessoryType = UITableViewCellAccessoryNone
        return cell
    
    # Below 2 methods conform to UITableViewDelegate protocol
    @objc_method
    def tableView_accessoryButtonTappedForRowWithIndexPath_(self, tv, indexPath):
        print("ACCESSORY TAPPED CALLED")
        pass
    
    @objc_method
    def tableView_didSelectRowAtIndexPath_(self, tv, indexPath):
        print("DID SELECT ROW CALLED FOR SECTION %s, ROW %s"%(str(indexPath.section),str(indexPath.row)))
        parent = gui.ElectrumGui.gui
        tv.deselectRowAtIndexPath_animated_(indexPath, True)
        tx = utils.nspy_get(self)
        isInput = tv.tag == self.tagin
        x = tx.inputs()[indexPath.row] if isInput else tx.get_outputs()[indexPath.row]
        vc = self.txDetailVC
        title = _("Options")
        message = _("Transaction Input {}").format(indexPath.row) if isInput else _("Transaction Output {}").format(indexPath.row)
        
        def getData(x, isAddr, isInput) -> str:
            data = ""
            if isAddr:
                if isInput:
                    addr = x['address']
                    if isinstance(addr, PublicKey):
                        addr = addr.toAddress()
                    if addr is None:
                        addr_text = _('unknown')
                    else:
                        addr_text = addr.to_ui_string()
                else:
                    addr, v = x
                    addr_text = addr.to_ui_string()
                data = addr_text
            elif isInput:
                prevout_hash = x.get('prevout_hash')
                prevout_n = x.get('prevout_n')
                data = prevout_hash[:] #+ ":%-4d" % prevout_n
            print("Data=%s"%str(data))
            return data
        
        def onCpy(isAddr : bool) -> None:
            print ("onCpy %s"%str(isAddr))
            parent.copy_to_clipboard(getData(x,isAddr,isInput))
        def onQR(isAddr : bool) -> None:
            print ("onQR %s"%str(isAddr))
            data = getData(x, isAddr, isInput)
            vc = self.txDetailVC
            qrvc = utils.present_qrcode_vc_for_data(vc, data)
            parent.add_navigation_bar_close_to_modal_vc(qrvc)

        def onBlkXplo() -> None:
            print ("onBlkXplo")
            if isInput:
                data = getData(x, False, True)
            else:
                data = getData(x, True, False)
                data = Address.from_string(data)
            parent.view_on_block_explorer(data, "tx" if isInput else "addr")
        
        actions = [
            [ _("Copy Address"), onCpy, True ],
            [ _("Show Address QR"), onQR, True ],
            [ _("Copy input hash"), onCpy, False ],
            [ _("Show input hash QR"), onQR, False ],
            [ _("View on block explorer"), onBlkXplo ],
            [ _("Cancel") ],
        ]
        if not isInput:
            actions.pop(2)
            actions.pop(2)
            # see if we have this output as a "Coin" in our wallet (UTXO)
            try:
                def get_name():
                    return str(tx.txid()) + (":%d"%indexPath.row)
                coin = coins.Find(get_name())
                if coin and self.txDetailVC.navigationController:
                    def onShowCoin(coin):
                        coins.PushCoinsDetailVC(coin, self.txDetailVC.navigationController)
                    actions.insert(0, [_("Show Coin Info"), onShowCoin, coin])
            except:
                print("Failed to get_name:",str(sys.exc_info()[1]))
            
        addy = getData(x, True, isInput)
        if addy and not isinstance(addy, Address):
            try:
                addy = Address.from_string(addy)
            except:
                addy = None
        if addy and parent.wallet:
            if parent.wallet.is_mine(addy):
                def onShowAddy(addy):
                    addresses.PushDetail(addy,self.txDetailVC.navigationController)
                
                actions.insert(0, [ _("Address Details"), onShowAddy, addy ] )
            elif addy.to_ui_string() not in parent.wallet.contacts.keys(): # is not mine, isn't in contacts, offer user the option of adding
                def doAddNewContact(addy):
                    from .contacts import show_new_edit_contact
                    show_new_edit_contact(addy, self.txDetailVC, onEdit=lambda x:utils.show_notification(_("Contact added")), title = _("New Contact"))
                actions.insert(1, [ _("Add to Contacts"), doAddNewContact, addy ] )
            elif self.txDetailVC.navigationController: # is not mine but is in contacts, so offer them a chance to view the contact
                def doShowContact(addy):
                    from .contacts import Find, PushNewContactDetailVC
                    entry = Find(addy)
                    if entry:
                        PushNewContactDetailVC(entry, self.txDetailVC.navigationController)
                actions.insert(1, [ _("Show Contact"), doShowContact, addy ] )

        
        utils.show_alert(vc = vc,
                         title = title,
                         message = message,
                         actions = actions,
                         cancel = _("Cancel"),
                         style = UIAlertControllerStyleActionSheet,
                         ipadAnchor = tv.convertRect_toView_(tv.rectForRowAtIndexPath_(indexPath), vc.view)
                         )
    

        
def CreateTxInputsOutputsTVC(txDetailVC : ObjCInstance, tx : Transaction, itv : ObjCInstance, otv : ObjCInstance, timestamp : float) -> ObjCInstance:
    tvc = TxInputsOutputsTVC.alloc()
    utils.nspy_put(tvc, tx)
    tvc = tvc.initWithInputTV_outputTV_timestamp_(itv,otv,timestamp).autorelease()
    tvc.txDetailVC = txDetailVC
    return tvc

# returns the view itself, plus the copy button and the qrcode button, plus the (sometimes nil!!) UITextField for the editable description
#  the copy and the qrcode buttons are so that caller may attach event handing to them
def setup_transaction_detail_view(vc : ObjCInstance) -> None:
    entry = utils.nspy_get_byname(vc, 'tx_entry')
    tx, tx_hash, status_str, label, v_str, balance_str, date, ts, conf, status, value, fiat_amount, fiat_balance, fiat_amount_str, fiat_balance_str, ccy, img, *dummy2 = entry
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    base_unit = parent.base_unit()
    format_amount = parent.format_amount
    #print("conf", conf,"label",label,"v_str",v_str,"date",date,"ts",ts,"status",status)
    if tx is None:
        tx = wallet.transactions.get(tx_hash, None)
        if tx is not None: tx.deserialize()
    if tx is None: raise ValueError("Cannot find tx for hash: %s"%tx_hash)
    tx_hash, status_, label_, can_broadcast, amount, fee, height, conf, timestamp, exp_n = wallet.get_tx_info(tx)
    size = tx.estimated_size()
    can_sign = not tx.is_complete() and wallet.can_sign(tx) #and (wallet.can_sign(tx) # or bool(self.main_window.tx_external_keypairs))
    
    #print("conf2",conf,"status_",status_,"label_",label,"amount",amount,"timestamp",timestamp,"exp_n",exp_n)

    wasNew = False
    if not vc.viewIfLoaded:
        NSBundle.mainBundle.loadNibNamed_owner_options_("TxDetail",vc,None)
        wasNew = True
    
    # grab all the views
    # Transaction ID:
    txTit = vc.txTit
    txHash =  vc.txHash
    copyBut = vc.cpyBut  
    qrBut =  vc.qrBut
    # Description:
    descTit = vc.descTit
    descTf = vc.descTf
    # Status:
    statusTit = vc.statusTit
    statusIV = vc.statusIV
    statusLbl = vc.statusLbl
    # Date:
    dateTit = vc.dateTit
    dateLbl = vc.dateLbl
    # Amount received/sent:
    amtTit = vc.amtTit
    amtLbl = vc.amtLbl
    # Size:
    sizeTit = vc.sizeTit
    sizeLbl = vc.sizeLbl
    # Fee:
    feeTit = vc.feeTit
    feeLbl = vc.feeLbl
    # Locktime:
    lockTit = vc.lockTit
    lockLbl = vc.lockLbl
    # Inputs
    inputsTV = vc.inputsTV
    # Outputs
    outputsTV = vc.outputsTV
    
    # Setup data for all the stuff
    txTit.text = _("Transaction ID:")
    tx_hash_str = tx_hash if tx_hash is not None and tx_hash != "None" and tx_hash != "Unknown" and tx_hash != _("Unknown") else _('Unknown')
    rbbs = []
    if can_sign:
        vc.noBlkXplo = True
        rbbs.append(UIBarButtonItem.alloc().initWithTitle_style_target_action_(_("Sign"), UIBarButtonItemStylePlain, vc, SEL(b'onSign')).autorelease())
        if not img:
            img = StatusImages[-1]
    if can_broadcast:
        vc.noBlkXplo = True
        rbbs.append(UIBarButtonItem.alloc().initWithTitle_style_target_action_(_("Broadcast"), UIBarButtonItemStylePlain, vc, SEL(b'onBroadcast')).autorelease())
        if not img:
            img = StatusImages[-2]
        
    if tx_hash == _("Unknown") or tx_hash is None: #unsigned tx
        txHash.text = tx_hash_str
        copyBut.setHidden_(True)
        qrBut.setHidden_(True)
        vc.notsigned = True
        txHash.userInteractionEnabled = False
        rbbs.append(UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemAction, vc, SEL(b'onShareSave:')).autorelease())
    else:
        copyBut.setHidden_(False)
        qrBut.setHidden_(False)
        vc.notsigned = False
        linkAttributes = {
            NSForegroundColorAttributeName : UIColor.colorWithRed_green_blue_alpha_(0.05,0.4,0.65,1.0),
            NSUnderlineStyleAttributeName : NSUnderlineStyleSingle              
        }
        txHash.attributedText = NSAttributedString.alloc().initWithString_attributes_(tx_hash_str, linkAttributes).autorelease()
        txHash.userInteractionEnabled = True
        if not txHash.gestureRecognizers:
            txHash.addGestureRecognizer_(UITapGestureRecognizer.alloc().initWithTarget_action_(vc,SEL(b'onTxLink:')).autorelease())
        rbbs.append(UIBarButtonItem.alloc().initWithBarButtonSystemItem_target_action_(UIBarButtonSystemItemAction, vc, SEL(b'onTxLink:')).autorelease())

    vc.navigationItem.rightBarButtonItems = rbbs 

    descTit.text = _("Description") + ":"
    descTf.text = label
    descTf.placeholder = _("Tap to add a description")
    if amount is not None and amount < 0:
        descTf.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(1.0,0.2,0.2,0.040)
    else:
        descTf.backgroundColor = UIColor.colorWithRed_green_blue_alpha_(0.0,0.0,1.0,0.040)
    descTf.adjustsFontSizeToFitWidth = True
    descTf.minimumFontSize = 8.0
    descTf.clearButtonMode = UITextFieldViewModeWhileEditing

    statusTit.text = _("Status:")
    if not img:
        #try and auto-determine the appropriate image if it has some confirmations and img is still null
        try:
            c = min(int(conf), 6)
            if c >= 0: img = StatusImages[c+3]
        except:
            pass
        if not img: img = UIImage.imageNamed_("empty.png")
    statusIV.image = img
    ff = str(status_) #status_str
    try:
        if int(conf) > 0:
           ff = "%s %s"%(str(conf), _('confirmations'))
    except:
        pass        
    statusLbl.text = _(ff)
    
    if timestamp or exp_n:
        if timestamp:
            dateTit.text = _("Date") + ":"
            dateLbl.text = str(date)
        elif exp_n:
            dateTit.text = _("Expected confirmation time") + ':'
            dateLbl.text = '%d blocks'%(exp_n) if exp_n > 0 else _('unknown (low fee)')
        vc.noBlkXplo = False
        dateTit.alpha = 1.0
        dateLbl.alpha = 1.0
    else:
        # wtf? what to do here? 
        dateTit.text = _("Date") + ":"
        dateLbl.text = ""
        dateTit.alpha = 0.5
        dateLbl.alpha = 0.5
 
    if amount is None:
        amtTit.text = _("Amount") + ":"
        amtLbl.text = _("Transaction unrelated to your wallet")
    elif amount > 0:
        amtTit.text = _("Amount received:")
        amtLbl.text = ('%s %s%s'%(format_amount(amount),base_unit,
                                  (" (" + fiat_amount_str + " " + ccy + ")") if fiat_amount_str else '',
                                  ))
    else:
        amtTit.text = _("Amount sent:") 
        amtLbl.text = ('%s %s%s'%(format_amount(-amount),base_unit,
                                  (" (" + fiat_amount_str.replace('-','') + " " + ccy + ")") if fiat_amount_str else '',
                                  ))

    sizeTit.text = _("Size:")
    if size:
        sizeLbl.text = ('%d bytes' % (size))
    else:
        sizeLbl.text = _("Unknown")

    feeTit.text = _("Fee") + ':'
    fee_str = '%s' % (format_amount(fee) + ' ' + base_unit if fee is not None else _('unknown'))
    if fee is not None:
        fee_str += '  ( %s ) '%  parent.format_fee_rate(fee/size*1000)
    feeLbl.text = fee_str
    
    if tx.locktime > 0:
        lockLbl.text = str(tx.locktime)

    # refreshes the tableview with data
    if wasNew:
        if ts is None: ts = time.time()
        tvc = CreateTxInputsOutputsTVC(vc, tx, inputsTV, outputsTV, float(ts))
    else:
        inputsTV.reloadData()
        outputsTV.reloadData()
        
class TxDetail(TxDetailBase):
    notsigned = objc_property() # by default is false.. if true, offer different buttons/options
    noBlkXplo = objc_property()
    cbTimer = objc_property()

    @objc_method
    def init(self) -> ObjCInstance:
        self = ObjCInstance(send_super(__class__, self, 'init'))
        if self:
            self.notsigned = False
            self.noBlkXplo = False
            self.title = _("Transaction") + " " + _("Details")

        return self
    
    @objc_method
    def dealloc(self) -> None:
        print("TxDetail dealloc")
        self.title = None
        self.view = None
        self.notsigned = None
        self.noBlkXplo = None
        if self.cbTimer: self.cbTimer.invalidate()
        self.cbTimer = None
        utils.nspy_pop(self)
        utils.remove_all_callbacks(self)
        send_super(__class__, self, 'dealloc')
    
    @objc_method
    def loadView(self) -> None:
        setup_transaction_detail_view(self)
            
    @objc_method
    def viewWillAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillAppear:', animated, argtypes=[c_bool])
        entry = utils.nspy_get_byname(self, 'tx_entry')
        self.descTf.text = entry.label
        #todo update this stuff in realtime?
        
    @objc_method
    def viewDidAppear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewDidAppear:', animated, argtypes=[c_bool])
        utils.get_callback(self, "on_appear")()

    @objc_method
    def viewWillDisappear_(self, animated : bool) -> None:
        send_super(__class__, self, 'viewWillDisappear:', animated, argtypes=[c_bool])

    @objc_method
    def textFieldShouldReturn_(self, tf : ObjCInstance) -> bool:
        #print("hit return, value is {}".format(tf.text))
        tf.resignFirstResponder()
        return True
    
    @objc_method
    def textFieldDidEndEditing_(self, tf : ObjCInstance) -> None:
        entry = utils.nspy_get_byname(self, 'tx_entry')
        tx_hash = entry.tx_hash
        tf.text = tf.text.strip()
        new_label = tf.text
        entry = utils.set_namedtuple_field(entry, 'label', new_label)
        utils.nspy_put_byname(self, entry, 'tx_entry')
        if tx_hash is not None:
            gui.ElectrumGui.gui.on_label_edited(tx_hash, new_label)
        utils.get_callback(self, 'on_label')(new_label)

    @objc_method
    def onCpyBut_(self, but) -> None:
        entry = utils.nspy_get_byname(self, 'tx_entry')
        gui.ElectrumGui.gui.copy_to_clipboard(entry.tx_hash)

    @objc_method
    def onQRBut_(self, but) -> None:
        #utils.show_notification(message="QR button unimplemented -- coming soon!", duration=2.0, color=(.9,0,0,1.0))
        
        entry = utils.nspy_get_byname(self, 'tx_entry')

        qrvc = utils.present_qrcode_vc_for_data(vc=self,
                                                data=entry.tx_hash,
                                                title = _('QR code'))
        gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(qrvc)

    @objc_method
    def onShareSave_(self, sender : ObjCInstance) -> None:
        parent = gui.ElectrumGui.gui        
        ipadAnchor = sender.view.frame if isinstance(sender, UIGestureRecognizer) else sender # else clause means it's a UIBarButtonItem
        if not parent.wallet: return
        tx = utils.nspy_get_byname(self, 'tx_entry').tx
        name = 'signed_%s.txt' % (tx.txid()[0:8]) if tx.is_complete() else 'unsigned.txt'
        fileName = utils.get_tmp_dir() + '/' + name
        text = None
        if fileName:
            tx_dict = tx.as_dict()
            input_values = [x.get('value') for x in tx.inputs()]
            tx_dict['input_values'] = input_values
            with open(fileName, "w+") as f:
                text = json.dumps(tx_dict, indent=4) + '\n'
                f.write(text)
            utils.NSLog("wrote tx - %d bytes to file: %s",len(text),fileName)
            text = None #No text.. 
        else:
            parent.show_error("Could not save transaction temp file")
            return           
        utils.show_share_actions(vc = self, fileName = fileName, text = text, ipadAnchor = ipadAnchor)
        
    @objc_method
    def onTxLink_(self, sender : ObjCInstance) -> None:
        entry = utils.nspy_get_byname(self, 'tx_entry')
        parent = gui.ElectrumGui.gui
        
        ipadAnchor = sender.view.frame if isinstance(sender, UIGestureRecognizer) else sender # else clause means it's a UIBarButtonItem

        def on_block_explorer() -> None:
            parent.view_on_block_explorer(entry.tx_hash, 'tx')

        actions = [
            [ _('Cancel') ],
            [ _('Copy to clipboard'), self.onCpyBut_, None ],
            [ _('Show as QR code'), self.onQRBut_, None ],
        ]
        if not self.noBlkXplo:
            actions.append([ _("View on block explorer"), on_block_explorer ])
         
            
        actions.append([_("Share/Save..."), lambda: self.onShareSave_(sender)])
            
        utils.show_alert(
            vc = self,
            title = _("Options"),
            message = _("Transaction ID:") + " " + entry.tx_hash[:12] + "...",
            actions = actions,
            cancel = _('Cancel'),
            style = UIAlertControllerStyleActionSheet,
            ipadAnchor = ipadAnchor
        )
        
    @objc_method
    def onSign(self) -> None:
        password = None
        parent = gui.ElectrumGui.gui
        wallet = parent.wallet
        if not wallet: return
        entry = utils.nspy_get_byname(self, 'tx_entry')
        tx = entry.tx

        if wallet.has_password():
            password = parent.password_dialog(_("Enter your password to proceed"))
            if not password:
                return

        def sign_done(success) -> None:
            nonlocal entry
            if success:
                tx_hash, *dummy = wallet.get_tx_info(tx)
                entry = utils.set_namedtuple_field(entry, 'tx_hash', tx_hash)
                utils.nspy_put_byname(self, entry, 'tx_entry')
                setup_transaction_detail_view(self) # recreate ui
            #else:
            #    parent.show_error(_("An Unknown Error Occurred"))
        parent.sign_tx_with_password(tx, sign_done, password)

    @objc_method
    def onBroadcast(self) -> None:
        parent = gui.ElectrumGui.gui
        wallet = parent.wallet
        if not wallet: return
        entry = utils.nspy_get_byname(self, 'tx_entry')
        tx = entry.tx
        
        def broadcastDone():
            nonlocal entry
            if self.viewIfLoaded is None:
                self.cbTimer = None
                return
            tx_hash, status_, label_, can_broadcast, amount, fee, height, conf, timestamp, exp_n = wallet.get_tx_info(tx)
            if conf is None:
                print("conf was none; calling broadcastDone again in 250 ms...")
                if self.cbTimer: self.cbTimer.invalidate()
                self.cbTimer = utils.call_later(0.250, broadcastDone)
                return
            else:
                print("conf was not none...refreshing TxDetail...")
            if self.cbTimer: self.cbTimer.invalidate()
            self.cbTimer = None
            status, status_str = wallet.get_tx_status(tx_hash, height, conf, timestamp)
            if status is not None and status >= 0 and status < len(StatusImages):
                entry = utils.set_namedtuple_field(entry, 'status_image', StatusImages[status])
                utils.nspy_put_byname(self, entry, 'tx_entry')
            setup_transaction_detail_view(self)
            
        parent.broadcast_transaction(tx, self.descTf.text, broadcastDone)
    
def CreateTxDetailWithEntry(entry : HistoryEntry, on_label = None, on_appear = None, tx = None, asModalNav = False) -> ObjCInstance:
    txvc = TxDetail.alloc()
    if not isinstance(entry.tx, Transaction) or isinstance(tx, Transaction):
        if isinstance(tx, Transaction):
            entry = utils.set_namedtuple_field(entry, 'tx', tx)
        else:
            raise ValueError('CreateWithEntry -- HistoryEntry provided must have an entry.tx that is a transaction!')
    utils.nspy_put_byname(txvc, entry, 'tx_entry')
    if callable(on_label): utils.add_callback(txvc, 'on_label', on_label)
    if callable(on_appear): utils.add_callback(txvc, 'on_appear', on_appear)
    txvc = txvc.init().autorelease()
    if asModalNav:
        gui.ElectrumGui.gui.add_navigation_bar_close_to_modal_vc(txvc,leftSide = True)
        return utils.tintify(UINavigationController.alloc().initWithRootViewController_(txvc).autorelease())
    return txvc

def CreateTxDetailWithTx(tx : Transaction, on_label = None, on_appear = None, asModalNav = False) -> ObjCInstance:
    parent = gui.ElectrumGui.gui
    wallet = parent.wallet
    import time

    tx_hash, status_, label_, can_broadcast, amount, fee, height, conf, timestamp, exp_n = wallet.get_tx_info(tx)
    size = tx.estimated_size()
    status_str = ""
    status = status_
    img = None
    if conf is not None:
        if tx_hash is not None and height is not None and timestamp is not None:
            status, status_str = wallet.get_tx_status(tx_hash, height, conf, timestamp)
            if status is not None and status >= 0 and status < len(StatusImages):
                img = StatusImages[status]
    else:
        conf = 0
    timestamp = time.time() if timestamp is None else timestamp
    doFX = False #fx() and fx().is_enabled()
    ccy = None #fx().get_currency() if doFX else None
    fiat_amount_str = None #str(self.fiat.text) if doFX else None 
    #HistoryEntry = namedtuple("HistoryEntry", "extra_data tx_hash status_str label v_str balance_str date ts conf status value fiat_amount fiat_balance fiat_amount_str fiat_balance_str ccy status_image")
    entry = HistoryEntry(tx,tx_hash,status_str,"",parent.format_amount(amount) if amount is not None else _("Transaction unrelated to your wallet"),
                         "",timestamp_to_datetime(time.time() if conf <= 0 else timestamp),
                         timestamp,conf,status,amount,None,None,fiat_amount_str,None,ccy,img)
      
    return CreateTxDetailWithEntry(entry, on_label = on_label, on_appear = on_appear, asModalNav = asModalNav)
