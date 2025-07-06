import React, {useEffect, useState} from 'react';

// Hardcoded config
const API_BASE_URL = 'http://localhost:8000';
const API_KEY = 'sms_backend_2025_secure_key_xyz789';

const apiHeaders = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

function App() {
    const [customers, setCustomers] = useState([]);
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [messages, setMessages] = useState([]);
    const [view, setView] = useState('customers'); // 'customers', 'conversation', 'add-customer'
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    // Load customers on startup
    useEffect(() => {
        loadCustomers();
    }, []);

    // Auto-refresh messages when viewing conversation
    useEffect(() => {
        if (selectedCustomer && view === 'conversation') {
            const interval = setInterval(() => {
                loadMessages(selectedCustomer.id);
            }, 3000);
            return () => clearInterval(interval);
        }
    }, [selectedCustomer, view]);

    const loadCustomers = async () => {
        try {
            setLoading(true);
            const response = await fetch(`${API_BASE_URL}/customers`, {
                headers: apiHeaders
            });
            if (response.ok) {
                const data = await response.json();
                setCustomers(data);
            } else {
                setError('Failed to load customers');
            }
        } catch (err) {
            setError('Error connecting to API: ' + err.message);
        } finally {
            setLoading(false);
        }
    };

    const loadMessages = async (customerId) => {
        try {
            const response = await fetch(`${API_BASE_URL}/messages?customer_id=${customerId}`, {
                headers: apiHeaders
            });
            if (response.ok) {
                const data = await response.json();
                setMessages(data);
            }
        } catch (err) {
            console.error('Error loading messages:', err);
        }
    };

    const selectCustomer = (customer) => {
        setSelectedCustomer(customer);
        setView('conversation');
        loadMessages(customer.id);
    };

    return (
        <div style={{padding: '20px', fontFamily: 'Arial, sans-serif'}}>
            <h1>💼 NextGen MedSpa Staff AI Service Tool</h1>

            {error && (
                <div style={{background: '#ffebee', color: '#c62828', padding: '10px', marginBottom: '20px'}}>
                    Error: {error}
                </div>
            )}

            <nav style={{marginBottom: '20px'}}>
                <button onClick={() => setView('customers')}>📋 Customers</button>
                <button onClick={() => setView('add-customer')}>➕ Add Customer</button>
                {selectedCustomer && (
                    <button onClick={() => setView('conversation')}>💬 Conversation: {selectedCustomer.name}</button>
                )}
            </nav>

            {loading && <div>Loading...</div>}

            {view === 'customers' &&
                <CustomerList customers={customers} onSelect={selectCustomer} onRefresh={loadCustomers}/>}
            {view === 'add-customer' && <AddCustomer onCustomerAdded={loadCustomers}/>}
            {view === 'conversation' && selectedCustomer && (
                <ConversationView
                    customer={selectedCustomer}
                    messages={messages}
                    onRefresh={() => loadMessages(selectedCustomer.id)}
                />
            )}
        </div>
    );
}

function CustomerList({customers, onSelect, onRefresh}) {
    const [customerStatuses, setCustomerStatuses] = useState({});
    const [loadingStatuses, setLoadingStatuses] = useState(false);
    const [deleting, setDeleting] = useState(null);
    const [statusMessage, setStatusMessage] = useState('');

    // Load status for all customers
    useEffect(() => {
        if (customers.length > 0) {
            loadCustomerStatuses();
        }
    }, [customers]); // eslint-disable-line react-hooks/exhaustive-deps

    const loadCustomerStatuses = async () => {
        setLoadingStatuses(true);
        const statuses = {};

        // Load messages for all customers in parallel
        const promises = customers.map(async (customer) => {
            try {
                const response = await fetch(`${API_BASE_URL}/messages?customer_id=${customer.id}`, {
                    headers: apiHeaders
                });
                if (response.ok) {
                    const messages = await response.json();
                    statuses[customer.id] = calculateStatus(messages);
                } else {
                    statuses[customer.id] = {status: 'error', color: '#666', icon: '❌'};
                }
            } catch (err) {
                statuses[customer.id] = {status: 'error', color: '#666', icon: '❌'};
            }
        });

        await Promise.all(promises);
        setCustomerStatuses(statuses);
        setLoadingStatuses(false);
    };

    const calculateStatus = (messages) => {
        if (messages.length === 0) {
            return {status: 'No Messages', color: '#666', icon: '⚫'};
        }

        const hasEscalation = messages.some(msg => msg.escalation);
        if (hasEscalation) {
            return {status: 'ESCALATED', color: '#d32f2f', icon: '🔴'};
        }

        // Check if AI is disabled due to staff taking over
        const lastOutboundMessage = messages.slice().reverse().find(msg => msg.direction === 'outbound');
        const isAIDisabled = lastOutboundMessage && lastOutboundMessage.source === 'manual';

        if (isAIDisabled) {
            return {status: 'AI Disabled', color: '#f57c00', icon: '🟠'};
        }

        return {status: 'AI Active', color: '#388e3c', icon: '🟢'};
    };

    const deleteCustomer = async (customer) => {
        if (!window.confirm(`Are you sure you want to delete ${customer.name}? This will also delete all their messages. This action cannot be undone.`)) {
            return;
        }

        setDeleting(customer.id);
        try {
            const response = await fetch(`${API_BASE_URL}/customers/${customer.id}`, {
                method: 'DELETE',
                headers: apiHeaders
            });

            if (response.ok) {
                const result = await response.json();
                setStatusMessage(`✅ ${result.message}`);
                onRefresh(); // Refresh the customer list
                setTimeout(() => setStatusMessage(''), 5000);
            } else {
                setStatusMessage('❌ Error deleting customer');
                setTimeout(() => setStatusMessage(''), 5000);
            }
        } catch (err) {
            setStatusMessage('❌ Error: ' + err.message);
            setTimeout(() => setStatusMessage(''), 5000);
        } finally {
            setDeleting(null);
        }
    };

    return (
        <div>
            <h2>📋 Customer List</h2>
            <button onClick={onRefresh}>🔄 Refresh</button>
            <button onClick={loadCustomerStatuses} disabled={loadingStatuses}>
                {loadingStatuses ? '🔄 Loading Statuses...' : '📊 Refresh Statuses'}
            </button>
            
            {statusMessage && (
                <div style={{
                    padding: '10px',
                    marginTop: '10px',
                    backgroundColor: statusMessage.includes('✅') ? '#e8f5e8' : '#ffebee',
                    color: statusMessage.includes('✅') ? '#2e7d2e' : '#c62828',
                    border: '1px solid ' + (statusMessage.includes('✅') ? '#4caf50' : '#f44336'),
                    borderRadius: '4px'
                }}>
                    {statusMessage}
                </div>
            )}

            {customers.length === 0 ? (
                <p>No customers found. Add some customers to get started!</p>
            ) : (
                <table border="1" style={{width: '100%', marginTop: '10px'}}>
                    <thead>
                    <tr>
                        <th>Name</th>
                        <th>Phone</th>
                        <th>Status</th>
                        <th>Tags</th>
                        <th>Notes</th>
                        <th>Action</th>
                    </tr>
                    </thead>
                    <tbody>
                    {customers.map(customer => {
                        const status = customerStatuses[customer.id];
                        return (
                            <tr key={customer.id}>
                                <td>{customer.name}</td>
                                <td>{customer.phone}</td>
                                <td style={{
                                    color: status?.color || '#666',
                                    fontWeight: 'bold',
                                    textAlign: 'center'
                                }}>
                                    {status ? `${status.icon} ${status.status}` : '🔄 Loading...'}
                                </td>
                                <td>{customer.tags?.join(', ') || 'None'}</td>
                                <td>{customer.notes || 'None'}</td>
                                <td>
                                    <button onClick={() => onSelect(customer)}>View Conversation</button>
                                    <button 
                                        onClick={() => deleteCustomer(customer)}
                                        disabled={deleting === customer.id}
                                        style={{
                                            marginLeft: '10px',
                                            backgroundColor: '#f44336',
                                            color: 'white',
                                            border: 'none',
                                            padding: '5px 10px',
                                            borderRadius: '4px',
                                            cursor: deleting === customer.id ? 'not-allowed' : 'pointer'
                                        }}
                                    >
                                        {deleting === customer.id ? '🔄 Deleting...' : '🗑️ Delete'}
                                    </button>
                                </td>
                            </tr>
                        );
                    })}
                    </tbody>
                </table>
            )}
        </div>
    );
}

function AddCustomer({onCustomerAdded}) {
    const [formData, setFormData] = useState({
        name: '',
        phone: '',
        notes: '',
        tags: ''
    });
    const [submitting, setSubmitting] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');

    const handleSubmit = async (e) => {
        e.preventDefault();
        setSubmitting(true);

        try {
            const customerData = {
                ...formData,
                tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : []
            };

            const response = await fetch(`${API_BASE_URL}/customers`, {
                method: 'POST',
                headers: apiHeaders,
                body: JSON.stringify(customerData)
            });

            if (response.ok) {
                setStatusMessage('✅ Customer added successfully!');
                setFormData({name: '', phone: '', notes: '', tags: ''});
                onCustomerAdded();
                setTimeout(() => setStatusMessage(''), 3000);
            } else {
                setStatusMessage('❌ Error adding customer');
                setTimeout(() => setStatusMessage(''), 5000);
            }
        } catch (err) {
            setStatusMessage('❌ Error: ' + err.message);
            setTimeout(() => setStatusMessage(''), 5000);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div>
            <h2>➕ Add New Customer</h2>
            {statusMessage && (
                <div style={{
                    padding: '10px',
                    marginBottom: '15px',
                    backgroundColor: statusMessage.includes('✅') ? '#e8f5e8' : '#ffebee',
                    color: statusMessage.includes('✅') ? '#2e7d2e' : '#c62828',
                    border: '1px solid ' + (statusMessage.includes('✅') ? '#4caf50' : '#f44336'),
                    borderRadius: '4px'
                }}>
                    {statusMessage}
                </div>
            )}
            <form onSubmit={handleSubmit}>
                <div style={{marginBottom: '10px'}}>
                    <label>Name: </label>
                    <input
                        type="text"
                        value={formData.name}
                        onChange={(e) => setFormData({...formData, name: e.target.value})}
                        required
                    />
                </div>

                <div style={{marginBottom: '10px'}}>
                    <label>Phone: </label>
                    <input
                        type="tel"
                        value={formData.phone}
                        onChange={(e) => setFormData({...formData, phone: e.target.value})}
                        placeholder="+1234567890"
                        required
                    />
                </div>

                <div style={{marginBottom: '10px'}}>
                    <label>Notes: </label>
                    <textarea
                        value={formData.notes}
                        onChange={(e) => setFormData({...formData, notes: e.target.value})}
                        rows="3"
                    />
                </div>

                <div style={{marginBottom: '10px'}}>
                    <label>Tags (comma separated): </label>
                    <input
                        type="text"
                        value={formData.tags}
                        onChange={(e) => setFormData({...formData, tags: e.target.value})}
                        placeholder="vip, botox, regular"
                    />
                </div>

                <button type="submit" disabled={submitting}>
                    {submitting ? 'Adding...' : 'Add Customer'}
                </button>
            </form>
        </div>
    );
}

function ConversationView({customer, messages, onRefresh}) {
    const [newMessageType, setNewMessageType] = useState('follow-up');
    const [newMessageContext, setNewMessageContext] = useState('');
    const [manualMessage, setManualMessage] = useState('');
    const [mockCustomerResponse, setMockCustomerResponse] = useState('');
    const [reEnableAI, setReEnableAI] = useState(false);
    const [submitting, setSubmitting] = useState(false);
    const [statusMessage, setStatusMessage] = useState('');

    const hasEscalation = messages.some(msg => msg.escalation);

    // Check if AI is disabled due to staff taking over
    const lastOutboundMessage = messages.slice().reverse().find(msg => msg.direction === 'outbound');
    const isAIDisabled = lastOutboundMessage && lastOutboundMessage.source === 'manual';

    const isAIActive = !hasEscalation && !isAIDisabled && messages.length > 0;

    const startConversation = async () => {
        setSubmitting(true);
        try {
            const response = await fetch(`${API_BASE_URL}/messages/initial/demo`, {
                method: 'POST',
                headers: apiHeaders,
                body: JSON.stringify({
                    name: customer.name,
                    message_type: newMessageType,
                    context: newMessageContext
                })
            });

            const result = await response.json();
            if (result.success) {
                setStatusMessage(`✅ AI Generated: "${result.response_content}"`);

                // Simulate saving the message
                await fetch(`${API_BASE_URL}/messages/manual`, {
                    method: 'POST',
                    headers: apiHeaders,
                    body: JSON.stringify({
                        customer_id: customer.id,
                        content: result.response_content,
                        direction: 'outbound',
                        source: 'ai'
                    })
                });

                onRefresh();
                setTimeout(() => setStatusMessage(''), 5000);
            }
        } catch (err) {
            setStatusMessage('❌ Error: ' + err.message);
            setTimeout(() => setStatusMessage(''), 5000);
        } finally {
            setSubmitting(false);
        }
    };

    const injectAIMessage = async () => {
        setSubmitting(true);
        try {
            const response = await fetch(`${API_BASE_URL}/messages/initial/demo`, {
                method: 'POST',
                headers: apiHeaders,
                body: JSON.stringify({
                    name: customer.name,
                    message_type: newMessageType,
                    context: newMessageContext
                })
            });

            const result = await response.json();
            if (result.success) {
                setStatusMessage(`✅ AI Message Injected: "${result.response_content}"`);

                // Save the AI-generated message
                await fetch(`${API_BASE_URL}/messages/manual`, {
                    method: 'POST',
                    headers: apiHeaders,
                    body: JSON.stringify({
                        customer_id: customer.id,
                        content: result.response_content,
                        direction: 'outbound',
                        source: 'ai'
                    })
                });

                onRefresh();
                setTimeout(() => setStatusMessage(''), 5000);
            }
        } catch (err) {
            setStatusMessage('❌ Error: ' + err.message);
            setTimeout(() => setStatusMessage(''), 5000);
        } finally {
            setSubmitting(false);
        }
    };

    const sendManualMessage = async () => {
        if (!manualMessage.trim()) return;

        setSubmitting(true);
        try {
            const response = await fetch(`${API_BASE_URL}/messages/manual/send`, {
                method: 'POST',
                headers: apiHeaders,
                body: JSON.stringify({
                    phone: customer.phone,
                    message_content: manualMessage,
                    re_enable_ai: reEnableAI
                })
            });

            const result = await response.json();
            if (result.success) {
                setManualMessage('');
                setReEnableAI(false);
                setStatusMessage(`✅ ${result.message}`);
                onRefresh();
                setTimeout(() => setStatusMessage(''), 5000);
            }
        } catch (err) {
            setStatusMessage('❌ Error: ' + err.message);
            setTimeout(() => setStatusMessage(''), 5000);
        } finally {
            setSubmitting(false);
        }
    };

    const mockCustomerReply = async () => {
        if (!mockCustomerResponse.trim()) return;

        setSubmitting(true);
        try {
            // Use the new ongoing/sms endpoint which handles escalation detection and auto-reply logic
            const response = await fetch(`${API_BASE_URL}/messages/ongoing/sms`, {
                method: 'POST',
                headers: apiHeaders,
                body: JSON.stringify({
                    phone: customer.phone,
                    message_content: mockCustomerResponse,
                    context: 'Customer response in demo mode'
                })
            });

            const result = await response.json();
            if (result.success) {
                if (result.message.includes('escalated') || result.message.includes('staff has taken over')) {
                    setStatusMessage(`⚠️ ${result.message}`);
                    setTimeout(() => setStatusMessage(''), 5000);
                } else {
                    setStatusMessage(`✅ Customer response processed`);
                    setTimeout(() => setStatusMessage(''), 3000);
                }
            }

            setMockCustomerResponse('');
            onRefresh();
        } catch (err) {
            setStatusMessage('❌ Error: ' + err.message);
            setTimeout(() => setStatusMessage(''), 5000);
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <div>
            <h2>💬 Conversation with {customer.name}</h2>
            <p><strong>Phone:</strong> {customer.phone}</p>
            <p><strong>Status:</strong>
                {hasEscalation && <span style={{color: 'red'}}> 🔴 ESCALATED - Manual Response Needed</span>}
                {isAIDisabled && !hasEscalation &&
                    <span style={{color: 'orange'}}> 🟠 AI Disabled - Staff Took Over</span>}
                {isAIActive && <span style={{color: 'green'}}> 🟢 AI Active</span>}
                {messages.length === 0 && <span style={{color: 'gray'}}> ⚫ No Messages</span>}
            </p>

            {statusMessage && (
                <div style={{
                    padding: '10px',
                    marginBottom: '15px',
                    backgroundColor: statusMessage.includes('✅') ? '#e8f5e8' :
                        statusMessage.includes('⚠️') ? '#fff3cd' : '#ffebee',
                    color: statusMessage.includes('✅') ? '#2e7d2e' :
                        statusMessage.includes('⚠️') ? '#856404' : '#c62828',
                    border: '1px solid ' + (statusMessage.includes('✅') ? '#4caf50' :
                        statusMessage.includes('⚠️') ? '#ffc107' : '#f44336'),
                    borderRadius: '4px'
                }}>
                    {statusMessage}
                </div>
            )}

            <button onClick={onRefresh}>🔄 Refresh Messages</button>

            {/* Message History */}
            <div style={{
                border: '1px solid #ccc',
                padding: '10px',
                margin: '20px 0',
                height: '300px',
                overflowY: 'scroll'
            }}>
                <h3>Message History:</h3>
                {messages.length === 0 ? (
                    <p>No messages yet. Start a conversation!</p>
                ) : (
                    messages.map((msg, index) => (
                        <div key={index} style={{
                            marginBottom: '10px',
                            padding: '8px',
                            backgroundColor: msg.direction === 'outbound' ? '#e3f2fd' : '#f3e5f5',
                            border: msg.escalation ? '2px solid red' : '1px solid #ddd'
                        }}>
                            <strong>{msg.direction === 'outbound' ? '📤 Us' : '📥 Customer'}:</strong> {msg.content}
                            <br/>
                            <small>Source: {msg.source} | Time: {new Date(msg.timestamp).toLocaleString()}</small>
                            {msg.escalation && (
                                <>
                                    <br/>
                                    <strong style={{color: 'red'}}>⚠️ ESCALATED</strong>
                                </>
                            )}
                        </div>
                    ))
                )}
            </div>

            {/* Start Conversation */}
            {messages.length === 0 && (
                <div style={{border: '1px solid #4caf50', padding: '15px', margin: '10px 0'}}>
                    <h3>🚀 Start AI Conversation</h3>
                    <div>
                        <label>Message Type: </label>
                        <select value={newMessageType} onChange={(e) => setNewMessageType(e.target.value)}>
                            <option value="welcome">Welcome</option>
                            <option value="follow-up">Follow-up</option>
                            <option value="reminder">Reminder</option>
                            <option value="promotional">Promotional</option>
                            <option value="support">Support</option>
                            <option value="thank-you">Thank You</option>
                            <option value="appointment">Appointment</option>
                        </select>
                    </div>
                    <div style={{marginTop: '10px'}}>
                        <label>Context: </label>
                        <input
                            type="text"
                            value={newMessageContext}
                            onChange={(e) => setNewMessageContext(e.target.value)}
                            placeholder="Had botox yesterday, checking in"
                            style={{width: '300px'}}
                        />
                    </div>
                    <button onClick={startConversation} disabled={submitting}>
                        {submitting ? 'Starting...' : '🚀 Start AI Conversation'}
                    </button>
                </div>
            )}

            {/* Inject AI Message - Available in ongoing conversations */}
            {messages.length > 0 && (
                <div style={{border: '1px solid #9c27b0', padding: '15px', margin: '10px 0'}}>
                    <h3>🤖 Inject AI Message</h3>
                    <p><em>Generate and send an AI message with a specific type/context:</em></p>
                    <div>
                        <label>Message Type: </label>
                        <select value={newMessageType} onChange={(e) => setNewMessageType(e.target.value)}>
                            <option value="welcome">Welcome</option>
                            <option value="follow-up">Follow-up</option>
                            <option value="reminder">Reminder</option>
                            <option value="promotional">Promotional</option>
                            <option value="support">Support</option>
                            <option value="thank-you">Thank You</option>
                            <option value="appointment">Appointment</option>
                        </select>
                    </div>
                    <div style={{marginTop: '10px'}}>
                        <label>Context: </label>
                        <input
                            type="text"
                            value={newMessageContext}
                            onChange={(e) => setNewMessageContext(e.target.value)}
                            placeholder="Check-in after treatment, special offer, etc."
                            style={{width: '300px'}}
                        />
                    </div>
                    <button onClick={injectAIMessage} disabled={submitting}>
                        {submitting ? 'Generating...' : '🤖 Generate & Send AI Message'}
                    </button>
                </div>
            )}

            {/* Mock Customer Response */}
            {messages.length > 0 && (
                <div style={{border: '1px solid #ff9800', padding: '15px', margin: '10px 0'}}>
                    <h3>📱 Mock Customer Response</h3>
                    <p><em>Simulate what the customer would text back:</em></p>
                    <textarea
                        value={mockCustomerResponse}
                        onChange={(e) => setMockCustomerResponse(e.target.value)}
                        placeholder="Hi! I have some swelling. Is that normal?"
                        rows="2"
                        style={{width: '100%'}}
                    />
                    <br/>
                    <button onClick={mockCustomerReply} disabled={submitting || !mockCustomerResponse.trim()}>
                        {submitting ? 'Processing...' : '📱 Send Customer Response (AI will auto-reply)'}
                    </button>
                </div>
            )}

            {/* Manual Staff Response */}
            <div style={{border: '1px solid #2196f3', padding: '15px', margin: '10px 0'}}>
                <h3>👩‍💼 Manual Staff Response</h3>
                <p><em>Override AI and send manual message:</em></p>
                <textarea
                    value={manualMessage}
                    onChange={(e) => setManualMessage(e.target.value)}
                    placeholder="Hi Sarah, this is Jessica from the clinic. I understand your concern..."
                    rows="3"
                    style={{width: '100%'}}
                />
                <br/>
                <div style={{marginTop: '10px'}}>
                    <label>
                        <input
                            type="checkbox"
                            checked={reEnableAI}
                            onChange={(e) => setReEnableAI(e.target.checked)}
                        />
                        {' '}Re-enable AI auto-reply after this message
                    </label>
                </div>
                <button onClick={sendManualMessage} disabled={submitting || !manualMessage.trim()}>
                    {submitting ? 'Sending...' : '👩‍💼 Send Manual Message'}
                </button>
            </div>
        </div>
    );
}

export default App;
