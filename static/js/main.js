class FacebookTools {
    constructor() {
        this.eventSource = new EventSource('/stream');
        this.logContainer = document.getElementById('logContainer');
        this.setupEventListeners();
        this.startFileListUpdater();
    }

    setupEventListeners() {
        this.eventSource.onmessage = this.handleLogMessage.bind(this);
        
        // Form cào thành viên
        const scrapeForm = document.getElementById('scrapeForm');
        const scrapeButton = document.getElementById('scrapeButton');
        const stopScrapeButton = document.getElementById('stopButton');
        
        scrapeForm.addEventListener('submit', this.handleScrapeSubmit.bind(this));
        stopScrapeButton.addEventListener('click', () => this.handleStop('scrape'));
        
        // Form kết bạn
        const addFriendsForm = document.getElementById('addFriendsForm');
        const addFriendsButton = document.getElementById('addFriendsButton');
        const stopAddFriendsButton = document.getElementById('stopAddFriendsButton');
        
        addFriendsForm.addEventListener('submit', this.handleAddFriendsSubmit.bind(this));
        stopAddFriendsButton.addEventListener('click', () => this.handleStop('addFriends'));
        
        // Xóa tài khoản
        document.querySelectorAll('.delete-account-btn')
            .forEach(btn => btn.addEventListener('click', this.handleDeleteAccount.bind(this)));
        
        // Thêm sự kiện cho nút edit
        document.querySelectorAll('.edit-account-btn')
            .forEach(btn => btn.addEventListener('click', this.handleEditAccount.bind(this)));
    }

    toggleButtons(action, isRunning) {
        const mainBtn = document.getElementById(`${action}Button`);
        const stopBtn = document.getElementById(action === 'scrape' ? 'stopButton' : 'stopAddFriendsButton');
        const form = document.getElementById(`${action}Form`);
        
        // Hiển thị/ẩn nút
        if (mainBtn) {
            mainBtn.style.display = isRunning ? 'none' : 'inline-block';
            mainBtn.disabled = isRunning;
        }
        
        if (stopBtn) {
            stopBtn.style.display = isRunning ? 'inline-block' : 'none';
            stopBtn.disabled = false; // Luôn enable nút dừng
        }
        
        // Disable/enable form
        if (form) {
            const elements = form.querySelectorAll('input, select');
            elements.forEach(el => {
                el.disabled = isRunning;
            });
        }
    }

    async handleStop(action) {
        const result = await Swal.fire({
            title: 'Xác nhận dừng',
            text: 'Bạn có chắc muốn dừng không?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Dừng lại',
            cancelButtonText: 'Hủy',
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#3b82f6',
            reverseButtons: true
        });

        if (!result.isConfirmed) return;
        
        const stopBtn = document.getElementById(action === 'scrape' ? 'stopButton' : 'stopAddFriendsButton');
        if (stopBtn) stopBtn.disabled = true;
        
        try {
            const response = await fetch('/stop_task', {
                method: 'POST'
            });
            const data = await response.json();
            
            if (data.success) {
                await this.showNotification({
                    title: 'Thành công',
                    text: data.message,
                    icon: 'success'
                });
                setTimeout(() => window.location.reload(), 1000);
            } else {
                throw new Error(data.message || 'Không thể dừng tiến trình');
            }
        } catch (error) {
            await this.showNotification({
                title: 'Lỗi',
                text: error.message,
                icon: 'error'
            });
            if (stopBtn) stopBtn.disabled = false;
        }
    }

    async handleScrapeSubmit(event) {
        event.preventDefault();
        const form = event.target;
        
        try {
            this.toggleButtons('scrape', true);
            const loading = this.showLoadingNotification('Đang cào dữ liệu...');
            
            const response = await fetch('/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    account_id: parseInt(form.account_id.value),
                    group_url: form.group_url.value,
                    max_members: form.max_members.value ? parseInt(form.max_members.value) : null
                })
            });

            const result = await response.json();
            loading.close();
            
            if (!result.success) {
                this.toggleButtons('scrape', false);
                await this.showNotification({
                    title: 'Lỗi',
                    text: result.error,
                    icon: 'error'
                });
            } else {
                await this.showNotification({
                    title: 'Thành công',
                    text: `Đã cào thành công ${result.members} thành viên!`,
                    icon: 'success'
                });
            }
        } catch (error) {
            this.toggleButtons('scrape', false);
            await this.showNotification({
                title: 'Lỗi',
                text: error.message,
                icon: 'error'
            });
        }
    }

    async handleAddFriendsSubmit(event) {
        event.preventDefault();
        const form = event.target;
        
        try {
            this.toggleButtons('addFriends', true);
            const loading = this.showLoadingNotification('Đang thêm bạn...');
            
            const response = await fetch('/add-friends', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    account_id: parseInt(form.account_id.value),
                    json_file: form.json_file.value,
                    max_friends: parseInt(form.max_friends.value)
                })
            });

            const result = await response.json();
            loading.close();
            
            if (!result.success) {
                this.toggleButtons('addFriends', false);
                await this.showNotification({
                    title: 'Lỗi',
                    text: result.error,
                    icon: 'error'
                });
            } else {
                await this.showNotification({
                    title: 'Thành công',
                    text: `Đã kết bạn thành công với ${result.added_friends} người!`,
                    icon: 'success'
                });
            }
        } catch (error) {
            this.toggleButtons('addFriends', false);
            await this.showNotification({
                title: 'Lỗi',
                text: error.message,
                icon: 'error'
            });
        }
    }

    async handleDeleteAccount(event) {
        const id = event.target.dataset.id;
        
        const result = await Swal.fire({
            title: 'Xác nhận xóa',
            text: 'Bạn có chắc muốn xóa tài khoản này?',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonText: 'Xóa',
            cancelButtonText: 'Hủy',
            reverseButtons: true
        });

        if (!result.isConfirmed) return;

        try {
            const response = await fetch(`/accounts/${id}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                await this.showNotification({
                    title: 'Thành công',
                    text: 'Đã xóa tài khoản',
                    icon: 'success'
                });
                window.location.reload();
            } else {
                throw new Error('Không thể xóa tài khoản');
            }
        } catch (error) {
            await this.showNotification({
                title: 'Lỗi',
                text: error.message,
                icon: 'error'
            });
        }
    }

    async handleEditAccount(event) {
        // Đảm bảo click event đúng target
        const button = event.target.closest('.edit-account-btn');
        if (!button) return;
        
        try {
            const accountData = button.dataset.account;
            if (!accountData) {
                throw new Error('Missing account data');
            }
            
            const accountObj = JSON.parse(accountData);
            this.showEditModal(accountObj);
        } catch (error) {
            this.showNotification({
                title: 'Lỗi',
                text: 'Không thể load thông tin tài khoản',
                icon: 'error'
            });
        }
    }

    showEditModal(account) {
        const modal = document.getElementById('editAccountModal');
        const form = document.getElementById('editAccountForm');
        
        if (!modal || !form) return;
        
        // Reset form
        form.reset();
        
        // Fill data
        form.name.value = account.name || '';
        form.cookie.value = account.cookie || '';
        form.dataset.accountId = account.id;
        
        // Show modal
        modal.classList.remove('hidden');
        
        // Focus first input
        form.name.focus();
        
        // Handle outside click
        const handleOutsideClick = (e) => {
            if (e.target === modal) {
                this.closeEditModal();
            }
        };
        
        // Handle Escape key
        const handleEscape = (e) => {
            if (e.key === 'Escape') {
                this.closeEditModal();
            }
        };
        
        modal.addEventListener('click', handleOutsideClick);
        document.addEventListener('keydown', handleEscape);
        
        // Clean up event listeners when modal closes
        const cleanup = () => {
            modal.removeEventListener('click', handleOutsideClick);
            document.removeEventListener('keydown', handleEscape);
        };
        
        modal.addEventListener('hidden', cleanup, { once: true });
    }

    closeEditModal() {
        const modal = document.getElementById('editAccountModal');
        const form = document.getElementById('editAccountForm');
        
        if (modal) {
            modal.classList.add('hidden');
        }
        
        if (form) {
            form.reset();
            delete form.dataset.accountId;
        }
    }

    async updateJsonFileList() {
        try {
            const accountSelect = document.querySelector('#addFriendsForm select[name="account_id"]');
            if (!accountSelect) return;
            
            const accountId = accountSelect.value;
            if (!accountId) return;

            // Hiển thị icon loading
            const refreshIcon = document.getElementById('jsonFileRefreshIcon');
            if (refreshIcon) {
                refreshIcon.classList.add('fa-spin');
            }

            const response = await fetch(`/get_json_files?account_id=${accountId}`);
            if (!response.ok) throw new Error('Không thể tải danh sách file');
            
            const files = await response.json();
            
            const select = document.querySelector('select[name="json_file"]');
            if (!select) return;

            if (Array.isArray(files) && files.length > 0) {
                select.innerHTML = files
                    .map(file => `<option value="${file}">${file}</option>`)
                    .join('');
            } else {
                select.innerHTML = '<option value="">Không có file nào</option>';
            }
                
        } catch (error) {
            const select = document.querySelector('select[name="json_file"]');
            if (select) {
                select.innerHTML = '<option value="">Lỗi tải danh sách file</option>';
            }
        } finally {
            // Tắt icon loading
            const refreshIcon = document.getElementById('jsonFileRefreshIcon');
            if (refreshIcon) {
                refreshIcon.classList.remove('fa-spin');
            }
        }
    }

    handleLogMessage(event) {
        if (event.data === '{}') return;
        
        const log = JSON.parse(event.data);
        const logElement = document.createElement('div');
        logElement.className = log.is_error ? 'text-red-500' : 'text-gray-700';
        logElement.textContent = `[${log.timestamp}] ${log.message}`;
        
        this.logContainer.appendChild(logElement);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }

    async showNotification({ title, text, icon = 'info', timer = 3000 }) {
        const Toast = Swal.mixin({
            toast: true,
            position: 'top-end',
            showConfirmButton: false,
            timer: timer,
            timerProgressBar: true,
            didOpen: (toast) => {
                toast.addEventListener('mouseenter', Swal.stopTimer)
                toast.addEventListener('mouseleave', Swal.resumeTimer)
            }
        });

        return Toast.fire({
            icon,
            title: text
        });
    }

    showLoadingNotification(text) {
        return Swal.fire({
            title: 'Đang xử lý',
            text,
            allowOutsideClick: true,
            allowEscapeKey: true,
            showConfirmButton: false,
            showCancelButton: true,
            cancelButtonText: 'Dừng lại',
            didOpen: () => {
                Swal.showLoading();
            }
        });
    }

    startFileListUpdater() {
        // Cập nhật khi thay đổi tài khoản
        const accountSelect = document.querySelector('#addFriendsForm select[name="account_id"]');
        if (accountSelect) {
            accountSelect.addEventListener('change', () => this.updateJsonFileList());
        }
        
        // Cập nhật định kỳ
        this.updateJsonFileList();
        setInterval(() => this.updateJsonFileList(), 5000);
    }
}

// Khởi tạo khi trang đã load
document.addEventListener('DOMContentLoaded', () => {
    new FacebookTools();
}); 